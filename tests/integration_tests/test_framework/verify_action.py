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

import os
import time
import threading
import numpy as np
import testsystem.constants as const
import test_framework.parsing as parsing
import test_framework as tf

from .action import Action
from .wait_action import WaitReportAction


class VerifyAction(Action):
    """
    This action verifies that the results from a report match the expected values.
    To see what the expected results are and what data this action verifies,
    look at the :py:class:`~test_framework.parsing.ExpectedResult` class.

    :param report_action: The report that should be verified.
    """

    def __init__(self, report_action: WaitReportAction):
        self.report_action = report_action

    def run(self):
        assert self.report_action.report is not None
        actual_result = self.report_action.report
        expected_result = self.report_action.commit_action.expected_result
        assert expected_result is not None, (
            "No result configuration for test case"
            f" '{self.report_action.commit_action.tc_name}'. If you use a verify action"
            " you must provide a valid result configuration. Add a result.json file to"
            f" the test case directory {self.report_action.commit_action.tc_path}."
        )
        if expected_result.total != actual_result.total:
            self.group.errors.append(
                "Expected total result for test case"
                f" '{self.report_action.commit_action.tc_name}' to be"
                f" {expected_result.total} but actual value is {actual_result.total}."
            )
        for ex_tc_result in expected_result.test_cases:
            for act_tc_result in actual_result.test_case_results:
                if ex_tc_result.id == act_tc_result.test_case_id:
                    if ex_tc_result.successful is not None:
                        if ex_tc_result.successful != act_tc_result.successful:
                            self.group.errors.append(
                                "Expected success state for test case"
                                f" '{self.report_action.commit_action.tc_name}' id"
                                f" {ex_tc_result.id} to be"
                                f" {ex_tc_result.successful} but actual state is"
                                f" {act_tc_result.successful}."
                            )
                    if ex_tc_result.result is not None:
                        if ex_tc_result.tolerance is None:
                            if ex_tc_result.result != act_tc_result.result:
                                self.group.errors.append(
                                    "Expected result for test case"
                                    f" '{self.report_action.commit_action.tc_name}' id"
                                    f" {ex_tc_result.id} to be"
                                    f" {ex_tc_result.result} but actual value is"
                                    f" {act_tc_result.result}."
                                )
                                continue
                        else:
                            if act_tc_result.result is None:
                                self.group.errors.append(
                                    "Expected result for test case"
                                    f" '{self.report_action.commit_action.tc_name}' id"
                                    f" {ex_tc_result.id}."
                                )
                                continue
                            tol = ex_tc_result.result * ex_tc_result.tolerance
                            dif = np.abs(ex_tc_result.result - act_tc_result.result)
                            if dif > tol:
                                if ex_tc_result.result != act_tc_result.result:
                                    self.group.errors.append(
                                        "Expected result for test case"
                                        f" '{self.report_action.commit_action.tc_name}'"
                                        f" id {ex_tc_result.id} to be within "
                                        f" {ex_tc_result.result - tol} and"
                                        f" {ex_tc_result.result + tol} but the actual"
                                        f" value is {act_tc_result.result}."
                                    )
                                    continue


class VerifyNoReportAction(Action):
    """
    Verifies that specific reports do not exist.
    It will assert that no report is published for a specific test case
    if the commit parameter is set.
    If no parameter is given, this action will verify that any report is published.

    :param commit: Optional commit for which a report should not exist.
    """

    def __init__(self, commit: tf.CommitAction | None = None):
        self.commit_action = commit

    def run(self):
        repo = self.group.repo
        repo.git.checkout(const.GIT_RESULT_BRANCH_NAME)
        commit_list = list(self.group.repo.iter_commits())
        for commit in commit_list:
            repo.git.checkout(commit)
            report_path = os.path.join(repo.working_dir, "reports", "README.md")  # type: ignore
            if not os.path.exists(report_path):
                continue
            with open(report_path, "r") as f:
                content = f.read()
            result = parsing.parse_group_report(content)
            if self.commit_action is None:
                assert result is None, (
                    "Expected to find no reports but found report for commit"
                    f" {result.tested_commit[0:8]}."
                )
            else:
                assert self.commit_action.commit_hash is not None
                if (
                    result is not None
                    and result.tested_commit[0:8] == self.commit_action.commit_hash[0:8]
                ):
                    assert False, (
                        "Expected to find no report for commit"
                        f" {result.tested_commit[0:8]} but this report does exist."
                    )
