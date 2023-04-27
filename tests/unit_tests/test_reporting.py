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

import re
import time
import pytest
import unittest.mock as mock
import testsystem.reporting as reporting
import testsystem.utils as utils


@mock.patch("testsystem.reporting._create_markdown_report_for_test_result")
def test_correct_order_in_markdown_report(m_create_report):
    def _create_report(test_case):
        return str(test_case.id)

    commit_hash = "1234"
    m_create_report.side_effect = _create_report
    tc1 = mock.MagicMock()
    tc2 = mock.MagicMock()
    tc3 = mock.MagicMock()
    tc4 = mock.MagicMock()
    tc1.tc_def.exercise_nr = 1
    tc1.id = 1
    tc1.test_case_id = 1
    tc2.tc_def.exercise_nr = 2
    tc2.id = 2
    tc2.test_case_id = 2
    tc3.tc_def.exercise_nr = 2
    tc3.id = 3
    tc3.test_case_id = 3
    tc4.tc_def.exercise_nr = 3
    tc4.id = 4
    tc4.test_case_id = 4
    test_results = [tc3, tc4, tc1, tc2]
    test_set_result = mock.MagicMock()
    test_set_result.test_results = test_results
    test_set_result.commit_hash = commit_hash
    test_set_result.commit_time = time.time() * 1000

    report = reporting.create_md_report_for_test_set(test_set_result)

    assert re.search(
        r"Exercise 1[\S\s]*1[\S\s]*Exercise 2[\S\s]*23[\S\s]*Exercise 3[\S\s]*4", report
    )


def mock_test_set(
    group_nr=1,
    tc_id=1,
    tc_ex_nr=1,
    tc_description="Test Case",
    result=1,
    commit_msg="Commit Message",
    commit_hash="0123abcd",
    successful=True,
    commit_time=1681204132,
    timestamp=1681204132,
):
    group = mock.MagicMock()
    group.group_nr = group_nr

    tc_def = mock.MagicMock()
    tc_def.id = tc_id
    tc_def.exercise_nr = tc_ex_nr
    tc_def.description = tc_description

    test_result = mock.MagicMock()
    test_result.tc_def = tc_def
    test_result.test_case_id = tc_def.id
    test_result.successful = successful
    test_result.result = result

    test_set = mock.MagicMock()
    test_set.group = group
    test_set.test_results = [test_result]
    test_set.commit_message = commit_msg
    test_set.commit_hash = commit_hash
    test_set.commit_time = commit_time
    test_set.timestamp = timestamp

    return test_set


def test_group_report_column_headers():
    test_set = mock_test_set()

    report = reporting._create_md_group_report_by_test_set(test_set)

    assert "|Id|Test Case|Deploy Process|Result|" in report


@pytest.mark.parametrize(
    "successful, result, col_value",
    [
        pytest.param(True, 1, "Completed", id="Successful Deployment"),
        pytest.param(False, None, "Failed", id="Failed Deployment"),
    ],
)
def test_group_report_deploy_process_value(successful, result, col_value):
    tc_name = "1st Test Case"
    tc_id = 7
    test_set = mock_test_set(
        result=result, tc_description=tc_name, tc_id=tc_id, successful=successful
    )

    report = reporting._create_md_group_report_by_test_set(test_set)

    assert f"|{tc_id}|{tc_name}|{col_value}|{str(result)}|" in report


timestamp = int(time.time()) * 1000
timestamp_str = utils.to_local_time_str(timestamp)


@pytest.mark.parametrize(
    "property, value, is_last",
    [
        pytest.param("Tested Commit", "0000FFFF", False, id="Tested Commit"),
        pytest.param("Commit Message", "Commit 1", False, id="Commit Message"),
        pytest.param("Commit Timestamp", timestamp_str, False, id="Commit Timestamp"),
        pytest.param("Test Timestamp", timestamp_str, False, id="Test Timestamp"),
        pytest.param("Total Points", 17, True, id="Total Points"),
    ],
)
@mock.patch("testsystem.reporting._create_md_group_stat_table")
def test_group_report_status_info(m_create_table, property, value, is_last):
    m_create_table.return_value = ("TABLE", 17)
    test_set = mock_test_set(
        commit_msg="Commit 1",
        commit_hash="0000FFFF",
        commit_time=timestamp,
        timestamp=timestamp,
    )

    report = reporting._create_md_group_report_by_test_set(test_set)
    expected = f"{property}: {value}"
    if is_last:
        expected += "\n\n"
    else:
        expected += "\\\n"

    assert expected in report
