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

import os
import logging
import time
import serial
import datetime
import numpy as np
import multiprocessing as mp
import testsystem.filesystem as fs
import testsystem.tool_chain as toolchain
import testsystem.filesystem as fs

from testsystem.models import MSP430, TestCase, PicoMeasure
from testsystem.utils import run_external_task
from testsystem.constants import (
    MSP430_FLASHER,
    MSP430_ELF_SIZE,
    TEST_MSP430_UART_BAUDRATE,
    TEST_TIMING_RUNS,
    TEST_MAX_TIMING_RETRIES,
    TEST_ACCEPTABLE_TIMING_VARIANCE_US,
    TEST_RETRIES,
    DEBUG_COLLECT_FAILED_BUILD_ARTEFACTS,
    DEBUG_FAILED_BUILD_ARTEFACTS_DIR,
)
from testsystem.exceptions import (
    MSPError,
    PicoError,
    TestCaseError,
    BuildError,
    FlashError,
    MSPConnectionError,
    ProcessError,
)

_mp_context = None


def _get_mp_context():
    global _mp_context
    if _mp_context is None:
        _mp_context = mp.get_context("forkserver")
    return _mp_context


def __power_down_msp(msp: MSP430):
    assert msp.debug_port
    args = [
        f"{MSP430_FLASHER}",
        "-e",
        "NO_ERASE",
        "-i",
        f"{os.path.basename(msp.debug_port)}",
        "-z",
        "[VCC=0]",
    ]
    code, _, err = run_external_task(args, timeout=30)
    if code != 0:
        raise MSPError(f"Failed to power down {msp}. {err}")


def __power_up_msp(msp: MSP430):
    assert msp.debug_port
    args = [
        f"{MSP430_FLASHER}",
        "-e",
        "NO_ERASE",
        "-i",
        f"{os.path.basename(msp.debug_port)}",
        "-z",
        "[VCC=3000]",
    ]
    code, _, err = run_external_task(args, timeout=30)
    if code != 0:
        raise MSPError(f"Failed to power up {msp}. {err}")


def __test_case_failed(tc: TestCase, warning: str = "", log: str = ""):
    logging.warning(
        f"Test case {tc.name} for group {tc.group_name} on {tc.msp} failed. {warning}"
    )
    tc.successful = False
    if len(log) == 0:
        log = warning
    tc.log += log


def __handle_flash_error(ex: FlashError, tc: TestCase):
    msg = f"Failed to flash test case {tc.name} to {tc.msp}. {ex.msg}"
    tc.result.flash_output = ex.output
    tc.result.flash_error = ex.error
    __test_case_failed(tc, msg)


def __handle_build_error(ex: BuildError, tc: TestCase):
    msg = f"Failed to build test case {tc.name}."
    tc.result.build_output = ex.output
    tc.result.build_error = ex.error
    __test_case_failed(tc, msg)


def measure_timing(tc: TestCase):
    """
    Measure the timing for a timing test case.
    """
    try:
        for _ in range(0, TEST_MAX_TIMING_RETRIES):
            results: list[float] = []
            for i in range(0, TEST_TIMING_RUNS):
                __power_down_msp(tc.msp)

                PicoMeasure.lock()
                try:
                    pico_measure = PicoMeasure(tc.pico)
                    pico_measure.start()

                    __power_up_msp(tc.msp)

                    try:
                        result = pico_measure.measure()
                        logging.debug(f"Timing result {i + 1}: {result}us")
                        results.append(result)
                    except TimeoutError:
                        logging.warn(
                            f"Timing test {tc.name} for group {tc.group_name} timed"
                            " out."
                        )
                    except PicoError as ex:
                        logging.warn(
                            f"Timing test {tc.name} for group {tc.group_name} failed."
                            f" {ex}"
                        )
                finally:
                    PicoMeasure.unlock()

            if len(results) == 0:
                tc.set_result(0)
                tc.successful = False
                return

            results_vector = np.array(results)
            timing_mean = np.mean(results_vector)
            timing_var = np.std(results_vector)

            if timing_var > TEST_ACCEPTABLE_TIMING_VARIANCE_US:
                logging.warning(
                    f"Too high timing variance {np.round(timing_var, 3)}us. Try to"
                    " improve the connection quality."
                )
                continue

            logging.info(
                f"Timing test result form {len(results)} runs: "
                f"mean={np.round(timing_mean, 3)}us "
                f"variance={np.round(timing_var, 3)}us."
            )
            tc.set_result(timing_mean)
            tc.successful = True
            return

        tc.successful = False
    except MSPError as ex:
        __test_case_failed(tc, ex.msg)


def measure_size(tc: TestCase):
    """
    Measure the size for a size test case.
    """
    elffilename = (
        f"{os.path.join(tc.directory, tc.name)}.msp430f5529.LaunchPad.{tc.group_name}.elf"
    )
    args = [f"{MSP430_ELF_SIZE}", f"{elffilename}", "-A"]
    code, out, err = run_external_task(args)
    if code == 0:
        try:
            # extract size from output
            line = out.splitlines(True)[-1]
            tc.set_result(int(line.split("Total")[1]))
            tc.successful = True
        except:
            __test_case_failed(tc, f"Failed to measure size.", f"{out}\n{err}")
    else:
        __test_case_failed(tc, f"Failed to measure size.", f"{out}\n{err}")


def run_test(tc: TestCase, test_env: fs.TestEnv):
    """
    Run a test case.
    """
    try:
        logging.debug(f"Run test {tc.name} for group {tc.group_name}.")

        tc.directory = fs.load_test_case(test_env, tc.name)
        toolchain.build_test_case(tc)
        if tc.timing:
            run_timing_test(tc)
        elif tc.size:
            run_size_test(tc)
        else:
            run_compare_test(tc)
    except TestCaseError as ex:
        __test_case_failed(tc, ex.msg, ex.msg)
    except BuildError as ex:
        if DEBUG_COLLECT_FAILED_BUILD_ARTEFACTS:
            dir_name = f"{test_env.group_name}-{test_env.commit_hash_short}-{tc.id}"
            dest = os.path.join(DEBUG_FAILED_BUILD_ARTEFACTS_DIR, dir_name)
            test_env.export(dest)
        __handle_build_error(ex, tc)
    finally:
        logging.debug(
            f"Test {tc.name} for group {tc.group_name} finished."
            f" Successful={tc.successful} Result={tc.result.result}"
        )


def run_compare_test(tc: TestCase, retries: int = TEST_RETRIES):
    """
    Run a standard (compare) test case.
    """

    def _retry(retries: int) -> bool:
        if retries <= 0:
            return False
        else:
            run_compare_test(tc, retries - 1)
            return True

    assert not tc.timing and not tc.size
    port = None

    try:
        port = serial.Serial(
            port=tc.msp.uart_port,
            baudrate=TEST_MSP430_UART_BAUDRATE,
            timeout=tc.runtime,
        )
    except:
        raise MSPConnectionError(
            f"Failed to open serial port {tc.msp.uart_port} on {tc.msp}."
        )

    try:
        toolchain.flash_test_case(tc)

        start = time.time()
        output = bytes(0)
        while time.time() - start < tc.runtime:
            output += port.read(16)
        output = output.decode("utf-8")
        tc.set_result(int(tc.compare_output(output)))
        tc.result.output = output
        tc.successful = True
    except FlashError as ex:
        __handle_flash_error(ex, tc)
    except UnicodeDecodeError as ex:
        if not _retry(retries):
            __test_case_failed(tc, "Failed to decode test case output.", str(ex))
    finally:
        port.close()


def _measure_timing_process(tc: TestCase, pipe):
    err = None
    for _ in range(0, TEST_RETRIES):
        try:
            measure_timing(tc)
            pipe.send(tc)
            return
        except Exception as ex:
            err = ex
            time.sleep(5)
    pipe.send(err)


def run_timing_test(tc: TestCase):
    """
    Run a timing test case.
    """
    assert tc.timing
    assert tc.test_unit.picoscope is not None

    ctx = _get_mp_context()

    try:
        toolchain.flash_test_case(tc)
        parent_conn, child_conn = mp.Pipe()
        process = ctx.Process(
            target=_measure_timing_process,
            args=(
                tc,
                child_conn,
            ),
        )
        process.start()
        logging.debug(f"Start timing measure in new process (PID={process.pid}).")
        while not parent_conn.poll(0.1) and process.is_alive():
            pass
        process.join()
        if process.exitcode == 0:
            logging.debug(
                f"Timing measure process (PID={process.pid}) finished as expected."
            )
            ret_val = parent_conn.recv()
            if isinstance(ret_val, TestCase):
                tc.successful = ret_val.successful
                tc.result.result = ret_val.result.result
                tc.log = tc.log
            elif isinstance(ret_val, Exception):
                raise ret_val
        else:
            raise ProcessError(
                f"Timing measure process (PID={process.pid}) failed. Exit code:"
                f" {process.exitcode}"
            )
    except FlashError as ex:
        __handle_flash_error(ex, tc)


def run_size_test(tc: TestCase):
    """
    Run a size test case.
    """
    assert tc.size
    try:
        toolchain.flash_test_case(tc)
        measure_size(tc)
    except FlashError as ex:
        __handle_flash_error(ex, tc)
