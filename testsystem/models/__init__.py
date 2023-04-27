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

# No model dependencies
from .msp430 import MSP430
from .pico_scope import PicoScope
from .test_case_def import TestCaseDef
from .uart_capture import UARTCapture

# Model dependencies
from .channel_reader import ChannelReader  # -> uart_capture
from .test_result import TestResult  # -> test_case_def
from .test_set import TestSet  # -> test_result
from .group import Group  # -> test_set
from .pico_reader import PicoReader  # -> pico_scope | channel_reader
from .connection_info import ConnectionInfo  # -> msp430 | pico_scope
from .test_unit import TestUnit  # -> msp430 | pico_scope | connection_info
from .pico_measure import PicoMeasure  # -> pico_scope | test_unit
from .task_worker import TaskWorker  # -> test_unit
from .task import Task  # -> test_unit
from .connection_detector import (
    ConnectionDetector,
)  # -> connection_info | msp430 | pico_reader | pico_scope | test_unit
from .test_case import TestCase  # -> group | test_result | test_unit | test_case_def
from .test_case_task import (
    TestCaseTask,
)  # -> task | test_case | test_unit | group | test_case_def
