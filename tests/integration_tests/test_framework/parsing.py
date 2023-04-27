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

import json
import re
import testsystem as ts

_result_regex = r"\|(?P<group_nr>[0-9]+)\|.*\[(?P<commit>[a-fA-F0-9]{8,}).*\].*\[(?P<success>[0-9]+).of.(?P<tests>[0-9]+).successful\].*"
_dgr_group_regex = r"Test Results for Group ([0-9]+)"
_dgr_commit_regex = r"Tested Commit: \[([0-9a-fA-F]{8,})\]"
_dgr_exercise_regex = (
    r"## Exercise (?P<exercise_nr>[0-9]+)(?P<exercise_content>[\s\S.]*?(?:(?=##"
    r" Exercise)|$))"
)
_dgr_tc_regex = (
    r"### Test Case (?P<tc_id>[0-9]+) (?P<status>[&#x0-9a-fA-F;]+)[\s]{2}.*Result:"
    r" (?P<result>[0-9None.,]+)"
)

_gr_group_regex = r"Test Results for Group ([0-9]+)"
_gr_commit_regex = r"Tested Commit: ([0-9a-fA-F]{8,})"
_gr_exercise_regex = (
    r"## Exercise (?P<exercise_nr>[0-9]+)(?P<exercise_content>[\s\S.]*?(?:(?=##"
    r" Exercise)|\Z))"
)
_gr_tc_regex = r"\|(?P<tc_id>[0-9]{1,3})\|.*\|(?P<successful>(?:True|False))\|(?P<result>[0-9.,None]*)\|"


class SysReportGroupResult:
    def __init__(
        self, group_nr: int, tested_commit: str, successful_tests: int, test_count: int
    ) -> None:
        self.group_nr = group_nr
        self.tested_commit = tested_commit
        self.successful = successful_tests
        self.test_count = test_count
        pass


class TestCaseResult:
    __test__ = False

    def __init__(
        self,
        test_case_id: int,
        result: float | None,
        exercise_nr: int,
        successful: bool | None,
    ) -> None:
        self.test_case_id = test_case_id
        self.result = result
        self.exercise_nr = exercise_nr
        self.successful = successful


class DetailedGroupResult:
    def __init__(
        self, group_nr: int, tc_results: list[TestCaseResult], tested_commit: str
    ) -> None:
        self.group_nr = group_nr
        self.tested_commit = tested_commit
        self.test_case_results = tc_results

    @property
    def total(self) -> int:
        sum = 0
        for r in self.test_case_results:
            if r.successful and r.result == 1.0:
                sum += 1
        return sum


class ExpectedTCResult:
    """
    Data class that contains information about what to expect from a single RTOS test
    case.

    :param id: The test case id as defined in the testcases.txt file.
    :param successful: Flag if the test case must be successful. Default value: ``None``
    :type successful: bool | None
    :param result: The expected result value for this test case. Default value: ``None``
    :type result: int | float | None
    :param tolerance: A tolerance margin for the result value between 0 and 1.
        This parameter could be helpful if you expect a timing result of ideally 100ms
        but want the test case to pass for values between 95ms and 105ms.
        In this case, you can set the tolerance property to 0.05.
        Default value: ``None``
    :type tolerance: float | None
    """

    def __init__(self, id: int, **kwargs) -> None:
        self.successful: bool | None = None
        self.result: int | float | None = None
        self.tolerance: float | None = None
        self.id = id
        for key, value in kwargs.items():
            if key == "successful":
                self.successful = value
            elif key == "result":
                self.result = value
            elif key == "tolerance":
                self.tolerance = value


class ExpectedResult:
    """
    Data class that contains information about what to expect from the test system. Add
    a JSON object of this class to each test case directory with the facts to verify in
    reports. A valid starting point for this JSON object could look like this:

    .. code-block:: javascript

        {
            "total": 5,                     // All test cases from ex1 should pass.
            "test_cases": [                 // But only one detailed result is asserted
                {
                    "id": 101,              // *sleep 100 ms* test case
                    "successful": true,
                    "result": 100000,
                    "tolerance": 0.0001     // Acceptable results: [99990, 100010]
                }
            ]
        }

    .. note::

        All parameters in the JSON file (except the test case id) are optional. You may
        only use the once that are useful in a specific scenario.

    :param total: The expected *total* result. Default value: ``0``
    :type total: int
    :param test_cases: A list of detailed RTOS test case results. This list does not
        require each RTOS test case but only the ones that are interesting for this
        specific test case. Default value: ``[]``
    :type test_cases: list[ExpectedTCResult]
    """

    def __init__(self, **kwargs) -> None:
        self.total: int = 0
        self.test_cases: list[ExpectedTCResult] = []

        for key, value in kwargs.items():
            if key == "total":
                self.total = value
            elif key == "test_cases":
                for tc in value:
                    self.test_cases.append(ExpectedTCResult(**tc))


def parse_sys_report_group_result(content: str) -> list[SysReportGroupResult]:
    results = []
    matches = re.finditer(_result_regex, content)
    for match in matches:
        dict = match.groupdict()
        group_nr = int(dict["group_nr"])
        commit = dict["commit"]
        success = int(dict["success"])
        tests = int(dict["tests"])
        if group_nr is not None and commit is not None and success is not None:
            result = SysReportGroupResult(
                group_nr, commit, successful_tests=success, test_count=tests
            )
            results.append(result)
    return results


def parse_detailed_group_report(content: str) -> DetailedGroupResult | None:
    """
    Parses the detailed group report which is published to the system repository. This
    is not the group report that the students get.

    :param content: The markdown content of the report.

    :returns: Detailed group result
    """
    group_match = re.search(_dgr_group_regex, content)
    commit_match = re.search(_dgr_commit_regex, content)
    if group_match is None or commit_match is None:
        return None
    group_nr = int(group_match.group(1))
    commit = commit_match.group(1)
    ex_matches = re.finditer(_dgr_exercise_regex, content)
    tc_results = []
    for ex_match in ex_matches:
        ex_dict = ex_match.groupdict()
        ex_nr = int(ex_dict["exercise_nr"])
        ex_content = ex_dict["exercise_content"]
        tc_matches = re.finditer(_dgr_tc_regex, ex_content)
        for tc_match in tc_matches:
            tc_dict = tc_match.groupdict()
            tc_id = int(tc_dict["tc_id"])
            status = tc_dict["status"]
            result_str = tc_dict["result"]
            if status == "&#x274c;":
                successful = False
            elif status == "&#x2705;":
                successful = True
            else:
                successful = None
            if result_str == "None":
                result = None
            else:
                result = float(result_str)
            tc_result = TestCaseResult(tc_id, result, ex_nr, successful)
            tc_results.append(tc_result)
    return DetailedGroupResult(group_nr, tc_results, commit)


def parse_group_report(content: str) -> DetailedGroupResult | None:
    """
    Parses a group report. This is the report that students find in their repository
    after they commited their os.

    :param content: The markdown content of the report.

    :returns: Detailed group result.
    """
    group_match = re.search(_gr_group_regex, content)
    commit_match = re.search(_gr_commit_regex, content)
    if group_match is None or commit_match is None:
        return None
    group_nr = int(group_match.group(1))
    commit = commit_match.group(1)
    ex_matches = re.finditer(_gr_exercise_regex, content)
    tc_results = []
    for ex_match in ex_matches:
        ex_dict = ex_match.groupdict()
        ex_nr = int(ex_dict["exercise_nr"])
        ex_content = ex_dict["exercise_content"]
        tc_matches = re.finditer(_gr_tc_regex, ex_content)
        for tc_match in tc_matches:
            tc_dict = tc_match.groupdict()
            tc_id = int(tc_dict["tc_id"])
            successful = ts.to_bool(tc_dict["successful"])
            result_str = tc_dict["result"]
            if result_str == "None":
                result = None
            else:
                result = float(result_str)
            tc_result = TestCaseResult(tc_id, result, ex_nr, successful)
            tc_results.append(tc_result)
    return DetailedGroupResult(group_nr, tc_results, commit)


def parse_expected_results(content: str) -> ExpectedResult | None:
    try:
        json_obj = json.loads(content)
    except json.JSONDecodeError:
        return None
    result = ExpectedResult(**json_obj)
    return result
