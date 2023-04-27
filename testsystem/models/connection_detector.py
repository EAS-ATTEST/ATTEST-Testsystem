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
import threading
import testsystem.tool_chain as tool_chain
import testsystem.filesystem as fs

from .connection_info import ConnectionInfo
from .msp430 import MSP430
from .pico_reader import PicoReader
from .pico_scope import PicoScope
from .test_unit import TestUnit

from testsystem.exceptions import (
    BuildError,
    DecodeError,
    PicoError,
    FlashError,
    FirmewareError,
    MSPConnectionError,
)
from testsystem.utils import get_uuid
from testsystem.constants import (
    MSP_ID_BAUD_RATE,
    MSP_ID_IDENTIFIER_PATH,
    MSP_ID_SAMPLES_PER_BIT,
    MSP_ID_START_PATTERN,
    LOG_INDENT,
)


def _get_id_parts(bytes: list[int]) -> tuple[int, int, int]:
    assert len(bytes) == 5
    device_id = (bytes[0] << 24) + (bytes[1] << 16) + (bytes[2] << 8) + bytes[3]
    port = (bytes[4] >> 4) & 0xF
    pin = bytes[4] & 0xF
    return device_id, port, pin


# TODO maybe include excluded ids to prevent duplicate generation
def _generate_id(start_pattern) -> int:
    """
    Generate a 32-bit id starting with the start_pattern. It is guaranteed that the
    start pattern won't appear in the other 3 bytes.

    :param start_pattern: 8-bit pattern to be used as most significant byte.
    """
    uuid = get_uuid()
    while (
        ((uuid >> 16) & 0xFF) == start_pattern
        or ((uuid >> 8) & 0xFF) == start_pattern
        or (uuid & 0xFF) == start_pattern
    ):
        uuid = get_uuid()
    return (uuid & 0xFFFFFF) + (start_pattern << 24)


def _decode_msp_info(bytes: list[int], start_pattern: int) -> tuple[int, int, int]:
    device_id = 0
    port = -1
    pin = -1
    find_start = True
    byte_set = []
    set_cnt = 0

    for i in range(len(bytes)):
        if find_start and bytes[i] == start_pattern:
            find_start = False
            byte_set.append(bytes[i])
        elif not find_start:
            byte_set.append(bytes[i])
            if len(byte_set) == 5:
                set_cnt += 1
                (
                    n_device_id,
                    n_port,
                    n_pin,
                ) = _get_id_parts(byte_set)

                if device_id == 0:
                    device_id = n_device_id
                elif device_id != n_device_id:
                    raise DecodeError(
                        f"Read inconsistent device ids (device_id={hex(device_id)},"
                        f" device_id={hex(n_device_id)} @ set_cnt={set_cnt})."
                    )

                if port < 0:
                    port = n_port
                elif port != n_port:
                    raise DecodeError(
                        f"Read inconsistent port numbers (port={port},"
                        f" port={n_port} @ set_cnt={set_cnt})."
                    )

                if pin < 0:
                    pin = n_pin
                elif pin != n_pin:
                    raise DecodeError(
                        f"Read inconsistent pin numbers (pin={pin}, pin={n_pin} @"
                        f" set_cnt={set_cnt})."
                    )

                find_start = True
                byte_set = []

    if set_cnt == 0:
        raise DecodeError(f"No valid device id found.")

    logging.debug(
        f"Successfully decoded UART signal containing {set_cnt} complete ids"
        f" (device_id={hex(device_id)} port={port} pin={pin})."
    )

    return device_id, port, pin


def _get_connections_from_channels(
    reader: PicoReader,
    picoscope: PicoScope,
    device_id_to_msp_map: dict[int, MSP430],
) -> list[ConnectionInfo]:
    connections = []
    for chnl_nr in range(16):
        pin_data = reader.get_channel_data(chnl_nr)
        if len(pin_data) >= 5:
            device_id, port, pin = _decode_msp_info(pin_data, MSP_ID_START_PATTERN)
            if device_id in device_id_to_msp_map.keys():
                connections.append(
                    ConnectionInfo(
                        port,
                        pin,
                        f"D{chnl_nr}",
                        device_id,
                        device_id_to_msp_map[device_id],
                        picoscope,
                    )
                )
            else:
                logging.warning(f"Read unknown id {hex(device_id)} from {picoscope}.")
    return connections


def _get_connections_from_picoscope(
    picoscope: PicoScope, device_id_to_msp_map: dict[int, MSP430]
) -> list[ConnectionInfo]:
    reader = PicoReader(picoscope)
    logging.debug(f"Reading MSP430 identification signal from {picoscope}.")
    connections: list[ConnectionInfo] = []
    try:
        for try_cnt in range(5):  # retry loop
            reader.read(MSP_ID_BAUD_RATE, MSP_ID_SAMPLES_PER_BIT, 500)
            try:
                connections = _get_connections_from_channels(
                    reader, picoscope, device_id_to_msp_map
                )
                break
            except DecodeError as ex:
                logging.warn(f"Failed to get connections on {try_cnt + 1}. try.")
    except PicoError as ex:
        logging.error(f"Reading from {picoscope} failed. {ex}")
    return connections


def _cleanup():
    try:
        for _, _, files in os.walk(MSP_ID_IDENTIFIER_PATH):
            for file in files:
                if file.startswith("_"):
                    try:
                        os.remove(os.path.join(MSP_ID_IDENTIFIER_PATH, file))
                    except OSError:
                        pass
    except Exception:
        pass


def _program_msp(msp: MSP430) -> int:
    """
    Program an MSP430 with the identifier program.

    :param msp: The MSP430 which is to be programmed.
    """
    try:
        id = _generate_id(MSP_ID_START_PATTERN)
        logging.debug(
            f"Programming {msp} for device identification with device_id {hex(id)}."
        )
        file = fs.create_msp430_identifier_program(id)
        target = file.replace(".c", "")
        tool_chain.build(
            MSP_ID_IDENTIFIER_PATH, [f"TARGET={target}", f"SOURCES={file}"]
        )
        hex_file = os.path.join(f"{MSP_ID_IDENTIFIER_PATH}", file.replace(".c", ".hex"))
        tool_chain.flash(msp, hex_file)
        return id
    finally:
        _cleanup()


class ConnectionDetector:
    """
    This class contains logic to identify connections between MSPs and PicoScopes
    and build test units out of them.

    :param msps: A list of available MSPs.
        These will identify themselves to PicoScopes through a unique id.
    :param picoscopes: A list of available PicoScopes.
        These will listen for MSP ids on their channels.
    """

    def __init__(self, msps: list[MSP430], picoscopes: list[PicoScope]):
        self.msps = msps
        self.picoscopes = picoscopes

    def get_test_units(self) -> list[TestUnit]:
        """
        Start the identification process and get valid combinations of MSPs and
        PicoScopes as test units.

        :returns: Returns a list of all identified test units.
        """
        if len(self.msps) == 0 or len(self.picoscopes) == 0:
            return []

        device_id_to_msp_map = self.__program_msps()
        if len(device_id_to_msp_map) == 0:
            logging.warning(
                "No MSP430 boards are flashed with an identifier program. Aborting"
                " discovery process."
            )
            return []

        connections = self.__get_connections(device_id_to_msp_map)
        TestUnit.set_connections(connections)
        self.__log_connections(connections)

        test_units = []
        for msp in device_id_to_msp_map.values():
            valid_test_unit = False
            for pico in self.picoscopes:
                valid, cons = TestUnit.validate_setup(msp, pico, connections)
                if valid:
                    test_units.append(TestUnit(msp, pico, cons))
                    valid_test_unit = True
                    break
            if not valid_test_unit:
                logging.info(
                    f"{msp} is not connected correctly to a PicoScope. This board will"
                    " be used without a PicoScope."
                )
                test_units.append(TestUnit(msp))

        return test_units

    def __program_msps(self) -> dict[int, MSP430]:
        device_id_to_msp_map = {}

        def prog_msp(msp):
            try:
                id = _program_msp(msp)
                if id != None:
                    device_id_to_msp_map[id] = msp
            except BuildError as ex:
                logging.info(f"{ex.error}")
                logging.error(f"Failed to build identification program. {ex.msg}")
            except FlashError as ex:
                logging.info(f"{ex.error}")
                logging.error(
                    f"Faile to flash identification program for {msp}. {ex.msg}"
                )
            except MSPConnectionError as ex:
                logging.error(ex.msg)
            except FirmewareError as ex:
                logging.error(ex.msg)

        logging.info("Flashing MSP430 boards with identification program.")
        program_threads: list[threading.Thread] = []
        for msp in self.msps:
            thread = threading.Thread(target=prog_msp, args=(msp,))
            thread.start()
            program_threads.append(thread)
        for thread in program_threads:
            thread.join()
        return device_id_to_msp_map

    def __get_connections(
        self, device_id_to_msp_map: dict[int, MSP430]
    ) -> list[ConnectionInfo]:
        logging.info("Reading identification signals from PicoScopes.")
        connections = []
        for pico in self.picoscopes:
            pico_conns = _get_connections_from_picoscope(pico, device_id_to_msp_map)
            for c in pico_conns:
                connections.append(c)
        return connections

    def __log_connections(self, connections: list[ConnectionInfo]):
        for msp in self.msps:
            msp_conns: list[ConnectionInfo] = []
            for c in connections:
                if c.msp430 == msp:
                    msp_conns.append(c)
            logging.info(f"{msp} has {len(msp_conns)} connections to PicoScopes:")
            for mc in msp_conns:
                logging.info(
                    f"{LOG_INDENT}MSP port {mc.msp_port} pin {mc.msp_pin} <--->"
                    f" {mc.picoscope} channel {mc.pico_channel}"
                )
