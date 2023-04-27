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
import testsystem.filesystem as fs
import testsystem.models as mdl

from subprocess import TimeoutExpired
from testsystem.utils import run_external_task
from testsystem.exceptions import (
    BuildError,
    FlashError,
    MSPConnectionError,
    FirmewareError,
)
from testsystem.constants import MSP430_FLASHER, MSP430_FLASHER_TIMEOUT_S


def build(src_dir: str, args: list[str]) -> str:
    """
    Build program with make..

    :raises BuildError: If building failed.

    :param src_dir: The directory of the makefile.

    :returns: The output from the build task.
    """
    _args = ["make", "-C", f"{src_dir}"] + args
    code, out, err = run_external_task(_args, timeout=10)
    if code == 0:
        return out
    else:
        raise BuildError(
            f"Failed to build {src_dir} with return code {code}.",
            output=out,
            error=err,
        )


def flash(msp: mdl.MSP430, file: str) -> str:
    """
    Flash a hex file onto an MSP430.

    :raises FlashError: If flashing failed.
    :raises MSPConnectionError: If connection to MSP430 failed.
    :raises FirmewareError: If the msp requires a firmeware update.

    :param file: Hex file to flash to MSP.

    :returns: The stdout from the flash task.
    """
    if msp.debug_port is None:
        raise MSPConnectionError(f"No debug port set for {msp}.")

    msp_port = os.path.basename(msp.debug_port)
    args = [
        f"{MSP430_FLASHER}",
        "-g",
        "-w",
        f"{file}",
        "-n",
        "msp430f5529",
        "-i",
        f"{msp_port}",
        "-z",
        "[VCC]",
    ]
    try:
        code, out, err = run_external_task(args, timeout=MSP430_FLASHER_TIMEOUT_S)
        if code == 0:
            msp.increment_flash_counter()
            return out
        else:
            raise FlashError(
                f"Failed to flash {msp} with return code {code}.",
                output=out,
                error=err,
            )
    except TimeoutExpired:
        connection_err_msg = (
            f"Flashing {msp} timed out. {MSP430_FLASHER} is stuck and does not respond."
        )
        try:
            # Try again to check if timeout was caused by missing firmeware update
            code, out, err = run_external_task(args, input="N", timeout=10)
            if code == 0 and "Warning: FW mismatch!" in out:
                raise FirmewareError(
                    f"The firmeware of {msp} is outdated. (Port: {msp_port})"
                )
            else:
                raise MSPConnectionError(connection_err_msg)
        except TimeoutExpired:
            raise MSPConnectionError(connection_err_msg)


def build_test_case(tc: mdl.TestCase):
    """
    Build test case from source.

    :raises BuildError: If building failed.

    :param tc: Test case.
    """
    tc.result.build_output = build(
        tc.directory,
        [
            f"PUBLIC={fs.get_public_repo_name()}",
            f"GROUP={tc.group_name}",
            "DEFINES=OS_ASSERTIONS",
        ],
    )


def flash_test_case(tc: mdl.TestCase):
    """
    Flash a test case onto an MSP430.

    :raises FlashError: If flashing failed.
    :raises MSPConnectionError: If connection to MSP430 failed.
    :raises FirmewareError: If the msp requires a firmeware update.

    :param tc: Test case to flash.
    """
    tc.result.flash_output = flash(
        tc.msp,
        os.path.join(
            tc.directory, f"{tc.name}.msp430f5529.LaunchPad.{tc.group_name}.hex"
        ),
    )
