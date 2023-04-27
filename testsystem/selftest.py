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

import re
import logging
import testsystem.constants as const

from testsystem.utils import run_external_task


def check_msp430_flasher() -> str | None:
    logging.debug("Check MSP430-Flasher installation.")
    code, output, err = run_external_task(const.MSP430_FLASHER)
    if code == 1:
        version = re.search(r"MSP Flasher v([0-9]+\.[0-9]+\.[0-9]+)", output).group(1)  # type: ignore
        logging.info(
            f"Found working MSP430-Flasher installation with version v{version}."
        )
        return version
    else:
        logging.error(f"MSP430-Flasher test exited with status code {code}. {err}")
        return None


def check_msp430_gcc() -> str | None:
    logging.debug("Check MSP430-GCC installation.")

    version_regex = r"msp430-gcc ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"
    code, output, err = run_external_task([f"{const.MSP430_ELF_GCC}", "--version"])
    if code == 0:
        gcc_version = re.search(version_regex, output).group(1)  # type: ignore
    else:
        logging.error(f"MSP430-GCC test exited with status code {code}. {err}")
        return None

    code, output, err = run_external_task([f"{const.MSP430_ELF_SIZE}", "--version"])
    if code == 0:
        size_version = re.search(version_regex, output).group(1)  # type: ignore
    else:
        logging.error(f"MSP430-GCC test exited with status code {code}. {err}")
        return None

    if gcc_version != size_version:
        logging.error(
            f"Version of {const.MSP430_ELF_GCC} and {const.MSP430_ELF_SIZE} does not"
            f" match ({gcc_version} != {size_version}).This is untested and could leat"
            " to problems."
        )
        return None

    logging.info(f"Found working MSP430-GCC installation with version {gcc_version}.")
    return gcc_version


def check_installations() -> bool:
    if not check_msp430_flasher():
        return False
    if not check_msp430_gcc():
        return False
    return True
