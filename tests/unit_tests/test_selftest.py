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

import unittest.mock as mock
import testsystem.selftest as selftest

@mock.patch('testsystem.selftest.run_external_task')
def test_check_msp430_flasher_successful(m_run_external_task):
    expected_version = "1.3.18"
    m_run_external_task.return_value = 1, f"... * /_ / MSP Flasher v{expected_version} * ...", None

    version = selftest.check_msp430_flasher()

    assert expected_version == version

@mock.patch('testsystem.selftest.run_external_task')
def test_check_msp430_flasher_failes(m_run_external_task):
    m_run_external_task.return_value = 139, None, "Segmentation fault (core dumped)"

    assert None == selftest.check_msp430_flasher()

@mock.patch('testsystem.selftest.run_external_task')
def test_check_msp430_gcc_successful(m_run_external_task):
    expected_version = "9.3.1.11"
    m_run_external_task.return_value = 0, f"msp430-elf-gcc (Mitto Systems Limited - msp430-gcc {expected_version}) 9.3.1", None

    version = selftest.check_msp430_gcc()

    assert expected_version == version

@mock.patch('testsystem.selftest.run_external_task')
def test_check_msp430_elf_gcc_fails(m_run_external_task):
    m_run_external_task.side_effect = [(127, None, "/bin/sh: 1: msp430-elf-gcc: not found"), 
        (0, f"GNU size (Mitto Systems Limited - msp430-gcc 9.3.1.11) 2.34", None)]
    assert None == selftest.check_msp430_gcc()

@mock.patch('testsystem.selftest.run_external_task')
def test_check_msp430_elf_size_fails(m_run_external_task):
    m_run_external_task.side_effect = [(0, f"msp430-elf-gcc (Mitto Systems Limited - msp430-gcc 9.3.1.11) 9.3.1", None),
        (127, None, "/bin/sh: 1: msp430-elf-size: not found")]
    assert None == selftest.check_msp430_gcc()

@mock.patch('testsystem.selftest.run_external_task')
def test_check_msp430_gcc_version_mismatch(m_run_external_task):
    version_gcc = "9.3.1.11"
    version_size = "10.0.0.0"
    m_run_external_task.side_effect = [(0, f"msp430-elf-gcc (Mitto Systems Limited - msp430-gcc {version_gcc}) 9.3.1", None),
        (0, f"GNU size (Mitto Systems Limited - msp430-gcc {version_size}) 2.34", None)]

    assert None == selftest.check_msp430_gcc()