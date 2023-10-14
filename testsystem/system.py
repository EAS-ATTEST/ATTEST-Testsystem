#
# Copyright 2023 EAS Group
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the “Software”), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from __future__ import annotations

import logging
import time
import testsystem.utils as utils
import testsystem.config as cnf
import testsystem.constants as const
import testsystem.selftest as selftest
import testsystem.filesystem as fs
import testsystem.reporting as reporting
import testsystem.scheduling as scheduling

from testsystem.device_discovery import discover_pico_scopes
from testsystem.models import (
    MSP430,
    PicoScope,
    TestUnit,
    TestSet,
    ConnectionDetector,
    TaskWorker,
    TestCaseDef,
)
from testsystem.constants import LOG_INDENT
from testsystem.config import get_config
from testsystem.exceptions import GitError


def _start_handler(func, *args):
    configure_logging()
    c = cnf.get_config()
    time.sleep(c.start_delay)
    print(const.TESTSYSTEM_TITLE)
    logging.info("Starting testsystem.")
    try:
        func(*args)
    except Exception as ex:
        logging.critical("Test system threw an exception.", exc_info=ex)
    logging.info("Shutting down testsystem.")


def _run_hello_testsystem():
    logging.info("Running Hello Testsystem")
    logging.info("Hello my dear friend!")
    if not selftest.check_installations():
        logging.error("OH NO! It seems something is missing.")
        return
    discover_msps()
    discover_picos()
    logging.info("##### EVERYTHING IS WORKING FINE #####")


def _set_device_name(serial_number: str, name: str):
    logging.info(f"Rename device {serial_number} to '{name}'.")
    logging.info(f"Try to find device with serial number {serial_number}.")
    device = MSP430.get_by_sn(serial_number)
    if device is None:
        device = PicoScope.get_by_sn(serial_number)
    if device is None:
        logging.warning(
            f"Could not find any device with serial number {serial_number}. Use the"
            " device on the testsystem first."
        )
        return
    device.set_name(name)
    logging.info(f"Device {device} is now called '{name}'.")


def discover_msps() -> list[MSP430]:
    msps = MSP430.get_connected()
    logging.info(f"Found {len(msps)} available MSP430 boards.")
    for msp in msps:
        logging.info(
            f"{LOG_INDENT}{msp} | UART Port: {msp.uart_port} | Debug Port:"
            f" {msp.debug_port}"
        )
    return msps


def discover_picos() -> list[PicoScope]:
    pico_scopes = discover_pico_scopes()
    logging.info(f"Found {len(pico_scopes)} available PicoScopes.")
    for pico in pico_scopes:
        logging.info(f"{LOG_INDENT}{pico}")
    return pico_scopes


def discover_process() -> tuple[list[TestUnit], list[MSP430], list[PicoScope]]:
    logging.info("Starting discovery process.")
    msps = discover_msps()
    pico_scopes = discover_picos()

    detector = ConnectionDetector(msps, pico_scopes)
    test_units = detector.get_test_units()
    logging.info(f"Found {len(test_units)} Test Units.")
    for tu in test_units:
        if tu.has_scope:
            logging.debug(
                f"{LOG_INDENT}{tu.msp430} and {tu.picoscope} are a valid Test Unit."
            )
        else:
            logging.debug(
                f"{LOG_INDENT}{tu.msp430} is used as Test Unit without a PicoScope."
            )
    logging.info("Discovery process finished.")
    return test_units, msps, pico_scopes


def _list_devices():
    msps = MSP430.get_all()
    logging.info(f"MSP430 boards ({len(msps)})")
    for msp in msps:
        logging.info(
            f"{LOG_INDENT}Name: {msp.name}, SN: {msp.serial_number}, Flash Counter:"
            f" {msp.flash_counter}"
        )
    picos = PicoScope.get_all()
    logging.info(f"PicoScopes ({len(picos)})")
    for pico in picos:
        logging.info(f"{LOG_INDENT}Name: {pico.name}, SN: {pico.serial_number}")


def _startup_routine() -> list[TestUnit]:
    logging.info("Test system now in startup routine.")
    if not selftest.check_installations():
        logging.error("Installation check failed.")
        exit(1)

    fs.init_fs()
    fs.load_public()
    TestSet.delete_unfinished_test_sets()

    test_units, msps, pico_scopes = discover_process()
    if len(test_units) == 0:
        logging.error("No Test Units found.")
        if len(pico_scopes) == 0:
            exit(2)
        else:
            exit(3)

    try:
        fs.publish_system_status_report(reporting.create_md_system_report())
    except GitError as ex:
        logging.error(ex.msg)
        exit(4)

    logging.info("Test system completed startup routine.")
    return test_units


def _idle():
    while True:
        time.sleep(1)
        conf = get_config()
        if conf.stop:
            break


def _schedule_group_tasks():
    test_units = _startup_routine()

    task_workers: list[TaskWorker] = []
    for i, tu in enumerate(test_units):
        worker = TaskWorker(tu, f"WORKER {i+1}")
        worker.start()
        task_workers.append(worker)

    scheduling.start()

    _idle()

    scheduling.stop()

    for worker in task_workers:
        worker.stop()


def _run():
    c = cnf.get_config()
    if utils.to_bool(c.run_hello_testsystem) == True:
        _run_hello_testsystem()
    else:
        _schedule_group_tasks()


def configure_logging():
    c = cnf.get_config()

    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler = logging.FileHandler(filename=c.log_file)
    file_handler.setLevel(level=c.log_level.upper())
    file_handler.setFormatter(file_formatter)

    stdout_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.setLevel(level=logging.INFO)

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stdout_handler])
    cnf.enable_logging()


def run_hello_testsystem():
    _start_handler(_run_hello_testsystem)


def run():
    _start_handler(_run)


def set_device_name(serial_number: str, name: str):
    _start_handler(_set_device_name, serial_number, name)


def list_devices():
    """
    Get a list of all MSPs and PicoScopes that have ever been connected to the test
    system.
    """
    _start_handler(_list_devices)


def startup_routine():
    """
    Execute only the startup routine. The test system will exit after startup.
    """
    _start_handler(_startup_routine)


def idle():
    """
    Start the test system in idle mode. The test system won't do anything in this mode.
    """
    _start_handler(_idle)
