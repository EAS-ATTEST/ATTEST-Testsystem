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

import pytest
import time
import unittest.mock as mock
import testsystem as ts
import testsystem.reporting as reporting
import test_framework.parsing as parsing


def test_parse_sys_report_group_result():
    # Arrange
    term = "SS00"
    group_name1 = ts.Group.get_name(11, term)
    group_name2 = ts.Group.get_name(12, term)
    group_name3 = ts.Group.get_name(13, term)
    group1 = ts.Group(group_nr=11, group_name=group_name1, term=term, active=True)
    group2 = ts.Group(group_nr=12, group_name=group_name2, term=term, active=True)
    group3 = ts.Group(group_nr=13, group_name=group_name3, term=term, active=True)
    test_result_1_1 = ts.TestResult(successful=True)
    test_result_2_1 = ts.TestResult(successful=False)
    test_result_2_2 = ts.TestResult(successful=True)
    test_set_1 = ts.TestSet(commit_hash="0011AABB", commit_message="Commit 1")
    test_set_1.test_results = [test_result_1_1]
    test_set_2 = ts.TestSet(commit_hash="ccdd3344", commit_message="Commit 1")
    test_set_2.test_results = [test_result_2_1, test_result_2_2]
    group1.get_latest_finished_test_set = mock.MagicMock(return_value=test_set_1)
    group2.get_latest_finished_test_set = mock.MagicMock(return_value=test_set_2)
    group3.get_latest_finished_test_set = mock.MagicMock(return_value=None)
    group1.get_priority = mock.MagicMock(return_value=10)
    group2.get_priority = mock.MagicMock(return_value=10)
    group3.get_priority = mock.MagicMock(return_value=10)
    groups = [group1, group2, group3]
    config = ts.get_config()
    report = reporting._get_group_table(groups, config)

    # Act
    results = parsing.parse_sys_report_group_result(report)

    # Assert
    assert 2 == len(results)
    assert "0011AABB" == results[0].tested_commit
    assert 1 == results[0].successful
    assert 1 == results[0].test_count
    assert 11 == results[0].group_nr
    assert "ccdd3344" == results[1].tested_commit
    assert 1 == results[1].successful
    assert 2 == results[1].test_count
    assert 12 == results[1].group_nr


@mock.patch("testsystem.models.test_result.TestCaseDef.get_all")
def test_parse_detailed_group_report(m_get_tcds):
    # Arrange
    group_nr = 1
    group_name = ts.Group.get_name(group_nr, "SS00")
    group = ts.Group(group_nr=group_nr, group_name=group_name)
    tc_def_1 = ts.TestCaseDef(id=10, exercise_nr=1)
    tc_def_2 = ts.TestCaseDef(id=11, exercise_nr=1)
    tc_def_3 = ts.TestCaseDef(id=201, exercise_nr=2)
    tc_def_4 = ts.TestCaseDef(id=301, exercise_nr=3)
    m_get_tcds.return_value = [tc_def_1, tc_def_2, tc_def_3, tc_def_4]
    test_result_1 = ts.TestResult(id=0, result=1, test_case_id=10, successful=True)
    test_result_2 = ts.TestResult(id=1, result=0, test_case_id=11, successful=False)
    test_result_3 = ts.TestResult(id=2, result=12345, test_case_id=201, successful=True)
    test_result_4 = ts.TestResult(id=3, result=None, test_case_id=301, successful=False)
    test_set = ts.TestSet(commit_hash="1122FFFF", commit_message="Fix")
    test_results = [test_result_1, test_result_2, test_result_3, test_result_4]
    test_set.test_results = test_results
    test_set.group = group
    test_set.commit_hash = "1234ABCD"
    test_set.commit_message = "Commit"
    test_set.commit_time = int(time.time() * 1000)
    report = reporting.create_md_report_for_test_set(test_set)

    # Act
    result = parsing.parse_detailed_group_report(report)

    # Assert
    assert result is not None
    assert 4 == len(result.test_case_results)
    assert test_set.commit_hash == result.tested_commit
    assert test_set.group.group_nr == group_nr

    for i in range(0, 4):
        assert test_results[i].test_case_id == result.test_case_results[i].test_case_id
        assert test_results[i].result == result.test_case_results[i].result
        assert test_results[i].successful == result.test_case_results[i].successful


@mock.patch("testsystem.models.test_result.TestCaseDef.get_all")
@mock.patch("testsystem.reporting.Group.get_by_term")
def test_parse_group_report(m_group_by_term, m_get_tcds):
    # Arrange
    group_nr = 1
    group_name = ts.Group.get_name(group_nr, "SS00")
    group = ts.Group(group_nr=group_nr, group_name=group_name)
    tc_def_1 = ts.TestCaseDef(id=10, exercise_nr=1)
    tc_def_2 = ts.TestCaseDef(id=11, exercise_nr=1)
    tc_def_3 = ts.TestCaseDef(id=20, exercise_nr=2)
    tc_def_4 = ts.TestCaseDef(id=30, exercise_nr=3)
    m_get_tcds.return_value = [tc_def_1, tc_def_2, tc_def_3, tc_def_4]
    test_result_1 = ts.TestResult(id=0, result=1, test_case_id=10, successful=True)
    test_result_2 = ts.TestResult(id=1, result=0, test_case_id=11, successful=False)
    test_result_3 = ts.TestResult(id=2, result=12345, test_case_id=20, successful=True)
    test_result_4 = ts.TestResult(id=3, result=None, test_case_id=30, successful=False)
    test_set = ts.TestSet(commit_hash="1122FFFF", commit_message="Fix")
    test_results = [test_result_1, test_result_2, test_result_3, test_result_4]
    test_set.test_results = test_results
    test_set.group = group
    test_set.commit_hash = "1234ABCD"
    test_set.commit_message = "Commit"
    test_set.commit_time = int(time.time() * 1000)
    test_set.timestamp = int(time.time() * 1000)
    m_group_by_term.return_value = []
    report = reporting.create_md_group_report(test_set)

    # Act
    result = parsing.parse_group_report(report)

    # Assert
    assert result is not None
    assert 4 == len(result.test_case_results)
    assert test_set.commit_hash == result.tested_commit
    assert test_set.group.group_nr == group_nr

    for i in range(0, 4):
        assert test_results[i].test_case_id == result.test_case_results[i].test_case_id
        assert test_results[i].result == result.test_case_results[i].result
        assert test_results[i].successful == result.test_case_results[i].successful


def test_parse_expected_total_result():
    # Arrange
    json_content = '{"total": 3}'

    # Act
    result = parsing.parse_expected_results(json_content)

    # Assert
    assert result is not None
    assert 3 == result.total


def test_parse_empty_expected_result():
    # Arrange
    json_content = ""

    # Act
    result = parsing.parse_expected_results(json_content)

    # Assert
    assert result is None


def test_parse_valid_empty_expected_result():
    # Arrange
    json_content = "{}"

    # Act
    result = parsing.parse_expected_results(json_content)

    # Assert
    assert result is not None
    assert 0 == result.total


def test_parse_expected_result_with_test_cases():
    # Arrange
    json_content = (
        '{"test_cases": [{"id": 1, "result": 7}, {"id": 2, "successful": true,'
        ' "result": 100, "tolerance": 0.01}]}'
    )

    # Act
    result = parsing.parse_expected_results(json_content)

    # Assert
    assert result is not None
    assert 0 == result.total
    assert 2 == len(result.test_cases)

    assert 1 == result.test_cases[0].id
    assert None == result.test_cases[0].successful
    assert 7 == result.test_cases[0].result
    assert result.test_cases[0].tolerance is None

    assert 2 == result.test_cases[1].id
    assert True == result.test_cases[1].successful
    assert 100 == result.test_cases[1].result
    assert 0.01 == result.test_cases[1].tolerance
