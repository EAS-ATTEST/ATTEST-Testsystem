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

import time
import logging
import numpy as np
import testsystem.testing as testing
import testsystem.filesystem as fs

from .task import Task
from .test_case import TestCase
from .test_unit import TestUnit
from .group import Group
from .test_case_def import TestCaseDef


class TestCaseTask(Task):
    """
    Test case task instance, which is scheduled and executed by the test system.
    """

    __test__ = False

    def __init__(
        self,
        group: Group,
        priority: float,
        test_case_def: TestCaseDef,
        test_env: fs.TestEnv,
        test_unit: TestUnit | None = None,
        test_unit_tag: str | None = None,
        callback=None,
        error_callback=None,
    ):
        self.group = group
        self.test_env = test_env
        self.test_case_def = test_case_def
        super().__init__(priority, test_unit, test_unit_tag, callback, error_callback)

    @property
    def test_case(self) -> TestCase:
        """
        The test case used by this task.
        This property is only valid after the task was executed.
        """
        assert self.__test_case is not None
        return self.__test_case

    def __repr__(self) -> str:
        return (
            "Test Case Task"
            f" (Name={self.test_case_def.name} Group={self.group.group_name} Priority={np.round(self.priority, 3)})"
        )

    def run(self):
        assert self.test_unit is not None
        self.group.add_queue_time(self.wait_time)
        logging.debug(
            f"Start test case {self.test_case_def.name} for group"
            f" {self.group.group_name}. This task spent {np.round(self.wait_time, 1)}s"
            " in queue."
        )
        self.__test_case = TestCase(self.test_case_def, self.group, self.test_unit)
        testing.run_test(self.__test_case, self.test_env)
