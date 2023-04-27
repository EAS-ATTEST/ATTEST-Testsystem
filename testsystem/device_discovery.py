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

import ctypes
import logging

from serial.tools.list_ports import comports
from picosdk.ps2000a import ps2000a as ps
from testsystem.models import MSP430, PicoScope
from testsystem.constants import PICO_ERROR_CODES
from testsystem.exceptions import MSPError


def discover_msp_boards() -> list[MSP430]:
    """
    Discover MSP boards connected to serial ports.

    :returns: Returns a list of available MSP430 boards.
    """
    logging.debug("Discover MSP430 boards.")
    c_ports = comports()
    logging.debug(f"Found {len(c_ports)} serial connections.")
    msps: list[MSP430] = []
    for p in c_ports:
        msp = None
        for m in msps:
            if m.serial_number == p.serial_number:
                msp = m
                break
        if msp is None:
            try:
                msp = MSP430.from_com_port(p)
                msps.append(msp)
            except MSPError as ex:
                logging.error(ex.msg)
        else:
            msp.patch(p)

    valid_msps: list[MSP430] = []
    for m in msps:
        if m.available:
            valid_msps.append(m)
        else:
            logging.warning(
                "MSP430 with only one com port found. Connect both devices (Debug and"
                f" UART interface) to use this board. ({m.get_identifier()})"
            )

    return valid_msps


def discover_pico_scopes_by_sn() -> list[str]:
    """
    Discover PicoScopes connected via USB.

    :returns: Returns a list of serial numbers for the available PicoScopes.
    """
    pico_cnt = ctypes.c_int16()

    sn_buf_len = ctypes.c_int16(4096)
    sn_buffer = ctypes.create_string_buffer(sn_buf_len.value)
    status = ps.ps2000aEnumerateUnits(  # type: ignore
        ctypes.byref(pico_cnt), sn_buffer, ctypes.byref(sn_buf_len)
    )
    logging.debug(
        f"API call enumerate picoscopes returned {PICO_ERROR_CODES[status][0]}."
        f" {PICO_ERROR_CODES[status][1]}"
    )
    return sn_buffer.value.decode().split(",")


def discover_pico_scopes() -> list[PicoScope]:
    """
    Discover PicoScopes connected via USB.

    :returns: Returns a list of available PicoScopes.
    """
    logging.debug("Discover Picoscopes.")
    pico_sn_list = discover_pico_scopes_by_sn()
    picos: list[PicoScope] = []

    for sn in pico_sn_list:
        if sn and sn.strip():
            pico = PicoScope.from_serial(sn)
            picos.append(pico)

    return picos
