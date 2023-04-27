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

from testsystem.filesystem import _create_msp_identifier_program
from testsystem.constants import MSP_ID_DEVICE_ID_TEMPLATE, MSP_ID_GENERATOR_DEFINE


def test_msp_identifier_program_generation():
    template = f"""
        #include <msp430f5529.h>
        #ifdef __RTS_GEN
        #define DEVICE_ID {MSP_ID_DEVICE_ID_TEMPLATE}
        #endif
    """
    device_id = 0xDEADBEAF
    program = _create_msp_identifier_program(template, device_id)  # type: ignore
    assert f"#define {MSP_ID_GENERATOR_DEFINE}" in program
    assert "#define DEVICE_ID 0xdeadbeaf" in program
