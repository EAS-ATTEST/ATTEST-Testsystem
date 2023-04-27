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

from testsystem.exceptions import ParsingError
from testsystem.config import get_config
from testsystem.filesystem import (
    get_test_case_definitions,
    get_expected_test_case_output,
)
from testsystem.constants import (
    TEST_ID_LENGTH,
    TEST_BEGIN_MARKER,
    TEST_NEVER_IN_OUTPUT,
)


_tc_defs = None


def parse(line: str) -> TestCaseDef:
    line = line.rstrip()
    regex = re.compile(
        r"#tc(?P<id>\d{3}): ex=(?P<ex>\d{2}) timing=(?P<timing>\d{1})"
        r" size=(?P<size>\d{1}) panic=(?P<panic>\d{1}) ranking=(?P<ranking>\d{1})"
        r' runtime=(?P<runtime>\d*) description="(?P<description>.*?)"'
    )
    match = regex.match(line)
    if not match:
        raise ParsingError(f"Invalid test case configuration.")

    id = int(match.group("id"))
    exercise_nr = int(match.group("ex"))
    runtime = int(match.group("runtime"))
    description = match.group("description")
    timing = int(match.group("timing")) == 1
    panic = int(match.group("panic")) == 1
    size = int(match.group("size")) == 1
    ranking = int(match.group("ranking")) == 1

    return TestCaseDef(
        id, exercise_nr, runtime, description, timing, panic, size, ranking
    )


def get_all(disable_cache: bool = False) -> list[TestCaseDef]:
    global _tc_defs
    if not disable_cache and _tc_defs is not None:
        return _tc_defs

    tcs = []
    lines = get_test_case_definitions().split("\n")
    for i in range(len(lines)):
        if lines[i].startswith("#"):
            try:
                tc = parse(lines[i])
                tcs.append(tc)
            except ParsingError as ex:
                logging.warning(f"Test case parsing error in line {i + 1}. {ex}")

    _tc_defs = tcs
    return _tc_defs


def get(disable_cache: bool = False) -> list[TestCaseDef]:
    conf = get_config()
    all_tests = get_all(disable_cache)
    active_tests = []
    for tc in all_tests:
        if tc.exercise_nr > conf.exercise_nr:
            continue
        if not conf.enable_timing_tests and tc.timing:
            continue
        active_tests.append(tc)
    return active_tests


def get_ranking_tests() -> list[TestCaseDef]:
    ranking_tests = []
    for tc_def in get():
        if tc_def.ranking:
            ranking_tests.append(tc_def)
    return ranking_tests


def get_max_exercise_nr() -> int:
    max = 0
    for tc_def in get_all():
        if tc_def.exercise_nr > max:
            max = tc_def.exercise_nr
    return max


class TestCaseDef:
    """
    RTOS test case definition class.
    Instances of this class are derived from the testcases.txt file.
    """

    __test__ = False

    def __init__(
        self,
        id: int = 0,
        exercise_nr: int = 0,
        runtime: int = 0,
        description: str = "",
        timing: bool = False,
        panic: bool = False,
        size: bool = False,
        ranking: bool = False,
    ):
        self.id = id
        self.exercise_nr = exercise_nr
        self.runtime = runtime
        self.description = description
        self.timing = timing
        self.panic = panic
        self.size = size
        self.ranking = ranking

    @property
    def name(self) -> str:
        return str(self.id).zfill(TEST_ID_LENGTH)

    def compare_output(self, output) -> bool:
        expected_output = get_expected_test_case_output(self.name)
        begin = output.find(TEST_BEGIN_MARKER)
        if begin == -1:
            return False

        output = output[begin:]

        if (
            output.find(expected_output) > -1
            and output.find(TEST_NEVER_IN_OUTPUT) == -1
        ):
            return True
        else:
            return False

    @classmethod
    def parse(cls, line: str) -> TestCaseDef:
        """
        Parses a line from the test case definitions into a
        :py:class:`testsystem.models.TestCaseDef` object.

        :exceptions ParsingError: Is raised if the config could not be parsed.

        :param line: A line from the test case definition file.

        :returns: A new test case definition instance.
        """
        return parse(line)

    @classmethod
    def get_all(cls) -> list[TestCaseDef]:
        """
        Load all parsable test case definitions. This does not account for configuration
        (exersice, timing, size, ...).

        :param disable_cache: Flag to disable caching.

        :returns: A list of test case definitions.
        """
        return get_all()

    @classmethod
    def get(cls) -> list[TestCaseDef]:
        """
        Load active test case definitions. This method accounts for config settings.

        :param disable_cache: Flag to disable caching.

        :returns: A list of test cases that should be used for test runs.
        """
        return get()

    @classmethod
    def get_ranking_tests(cls) -> list[TestCaseDef]:
        """
        Get a list of active ranking test cases.

        :returns: A list of all ranking tests.
        """
        return get_ranking_tests()

    @classmethod
    def get_max_exercise_nr(cls) -> int:
        """
        Get the highest exercise number found in test case definitions.

        :returns: The highest exercise number.
        """
        return get_max_exercise_nr()

    @classmethod
    def get_by_id(cls, id: int) -> TestCaseDef | None:
        """
        Get a test case by its test case number.

        :param id: Test case id.

        :returns: Returns the test case definition or None if it does not exist.
        """
        for tc in get_all():
            if tc.id == id:
                return tc
        return None
