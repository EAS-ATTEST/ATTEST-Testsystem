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

import testsystem.tool_chain as tool_chain
import unittest.mock as mock
import pytest

from subprocess import TimeoutExpired
from testsystem.exceptions import FirmewareError, MSPConnectionError


@mock.patch("testsystem.tool_chain.run_external_task")
def test_flash_msp_with_outdated_firmware(m_ext_task):
    def side_effect_func(args, input=None, timeout=10):
        stdout = (
            "* Checking firmware compatibility: "
            "* The firmware of your FET is outdated."
            "- Would you like to update it? (Y/N): N"
            "* Warning: FW mismatch! Correct functionality not guaranteed!"
        )
        if input != "N":
            raise TimeoutExpired("", timeout)
        else:
            return 0, stdout, ""

    m_ext_task.side_effect = side_effect_func
    m_msp = mock.MagicMock()
    m_msp.increment_flash_counter = mock.MagicMock()
    m_msp.debug_port = "/dev/ttyACM0"

    with pytest.raises(FirmewareError):
        tool_chain.flash(m_msp, "")


@mock.patch("testsystem.tool_chain.run_external_task")
def test_flash_msp_with_outdated_firmware_times_out(m_ext_task):
    def side_effect_func(args, input=None, timeout=10):
        raise TimeoutExpired("", timeout)

    m_ext_task.side_effect = side_effect_func
    m_msp = mock.MagicMock()
    m_msp.increment_flash_counter = mock.MagicMock()
    m_msp.debug_port = "/dev/ttyACM0"

    with pytest.raises(MSPConnectionError) as ex:
        tool_chain.flash(m_msp, "")
        assert "Timeout" in ex.value.msg
