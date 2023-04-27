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

import traceback
import time
import logging

from .test_unit import TestUnit


class Task:
    """
    The base class for all tasks.

    :param priority: The priority for the task. Lower value means higher priority.
    :param test_unit: If specified, the task may only run on this test unit.
    :param tag: If specified, the task my only run on a test unit with the specific tag.
    :param callback: A function of type func(Task), which is called on successful
        completion of the task.
    :param error_callback: A function of type func(Task, Exception), which is called
        when the task fails.
    """

    schedule_time = 0.0
    start_time = 0.0
    finish_time = 0.0

    def __init__(
        self,
        priority: float = 100,
        test_unit: TestUnit | None = None,
        tag: str | None = None,
        callback=None,
        error_callback=None,
    ):
        self.priority = priority
        self.test_unit: TestUnit | None = None
        self.specific_test_unit = test_unit
        self.test_unit_tag = tag
        self.callback = callback
        self.error_callback = error_callback
        self.__active = False
        self.__finished = False

    @property
    def use_specific_test_unit(self) -> bool:
        """
        Flag if this task must use a specific test unit.
        """
        return self.specific_test_unit is not None

    @property
    def use_tagged_test_unit(self) -> bool:
        """
        Flag if this task must use a test unit with a specific tag.
        """
        return self.test_unit_tag is not None

    @property
    def runtime(self) -> float:
        """
        Time between start and finish of the task.
        """
        return self.finish_time - self.start_time

    @property
    def wait_time(self) -> float:
        """
        Time between scheduling and start in seconds.
        """
        return self.start_time - self.schedule_time

    def __repr__(self) -> str:
        return f"Priority {self.priority} Task"

    def run_safe(self, test_unit: TestUnit):
        assert not self.__active
        assert not self.__finished

        if self.use_specific_test_unit:
            assert test_unit == self.specific_test_unit

        if self.test_unit_tag is not None:
            assert test_unit.has_tag(self.test_unit_tag)

        self.test_unit = test_unit
        self.__active = True

        self.start_time = time.time()
        self.finish_time = 0.0
        try:
            self.run()
            self.finish_time = time.time()
            self.__callback()
            self.__finished = True
        except Exception as err:
            self.finish_time = time.time()
            self.__err_callback(err)
        finally:
            self.__active = False

    def run(self):
        """
        Override this method to implement the tasks functionallity.
        """
        pass

    def __callback(self):
        if self.callback is None:
            return

        try:
            self.callback(self)
        except Exception as ex:
            logging.error(f"Task callback failed. {ex}")
            traceback.print_exception(type(ex), ex, ex.__traceback__)

    def __err_callback(self, err: Exception):
        if self.error_callback is None:
            return

        try:
            self.error_callback(self, err)
        except Exception as ex:
            logging.error(f"Task error callback failed. {ex}")
            logging.error(
                f"The actual error which caused the call to error callback: {err}"
            )
            traceback.print_exception(type(err), err, err.__traceback__)
