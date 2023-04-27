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

from .group import Group
from .test_result import TestResult
from .test_unit import TestUnit, MSP430, PicoScope
from .test_case_def import TestCaseDef


class TestCase:
    """
    Instance of a test case definition which holds information for a specific test run.
    """

    __test__ = False

    def __init__(self, definition: TestCaseDef, group: Group, test_unit: TestUnit):
        self.definition = definition
        self.group = group
        self.test_unit = test_unit
        self.directory: str = ""
        self.result = TestResult(
            test_case_id=definition.id,
            successful=False,
        )
        self.log: str = ""

    @property
    def id(self) -> int:
        return self.definition.id

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def exercise_nr(self) -> int:
        return self.definition.exercise_nr

    @property
    def runtime(self) -> int:
        return self.definition.runtime

    @property
    def description(self) -> str:
        return self.definition.description

    @property
    def timing(self) -> bool:
        return self.definition.timing

    @property
    def panic(self) -> bool:
        return self.definition.panic

    @property
    def size(self) -> bool:
        return self.definition.size

    @property
    def ranking(self) -> bool:
        return self.definition.ranking

    @property
    def group_name(self) -> str:
        return self.group.group_name

    @property
    def msp(self) -> MSP430:
        return self.test_unit.msp430

    @property
    def pico(self) -> PicoScope:
        return self.test_unit.picoscope

    @property
    def env_id(self) -> str:
        return self.test_unit.msp430.serial_number

    @property
    def successful(self) -> bool:
        return self.result.successful

    @successful.setter
    def successful(self, value):
        self.result.successful = value

    @property
    def timestamp(self) -> int:
        return self.result.timestamp

    @timestamp.setter
    def timestamp(self, value: int):
        self.result.timestamp = value

    def set_result(self, result):
        self.result.result = result

    def compare_output(self, output) -> bool:
        """
        Method to compare the output of a test case with the expected output.

        :returns: ``True`` if the output is as expected, ``False`` otherwise.
        """
        return self.definition.compare_output(output)
