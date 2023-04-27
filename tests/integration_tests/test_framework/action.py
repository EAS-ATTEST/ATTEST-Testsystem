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

import sys
import logging
import traceback

import test_framework as tf


class Action:
    """
    This is the base class for all actions executed by a group model.
    It has some convenience methods to chain action methods for a group.

    :param group: Reference to this actions group model.
    """

    def set_group(self, group: tf.GroupModel):
        self.group = group

    def run_save(self):  # type: ignore
        assert self.group is not None, "Group is not initialized for this action."
        try:
            self.run()
        except:
            last_type, last_value, _ = sys.exc_info()
            traceback.print_exc()
            logging.error("[TEST] Test action failed.")
            self.group.errors.append(f"{type(last_type).__name__}: {last_value}")

    def run(self):
        pass

    def stop_test_system(self) -> tf.StopTestsystemAction:
        """
        Adds an action to stop and shutdown the test system.
        """
        return self.group.stop_test_system()

    def commit(self, tc_name: str, commit_msg: str | None = None) -> tf.CommitAction:
        """
        Adds a commit action.
        The data to commit is specified by the parameter **tc_name**,
        the name of a directory in data/test_cases.
        To get more information about the directory structure take a look at the
        :py:class:`~test_framework.CommitAction` constructor.

        :param tc_name: The name of the directory containing the data to be commited.
        :param commit_msg: An optional commit message. IF not set, the commit message
            will be the tc_name.

        :returns: Commit action.
        """
        return self.group.commit(tc_name, commit_msg)

    def initial_commit(
        self, tc_name: str, commit_msg: str | None = None
    ) -> tf.InitialCommitAction:
        """
        Adds an initial commit action that is already present
        when the test system starts.
        The data to commit is specified by the parameter tc_name,
        which is the name of a directory in data/test_cases.

        :param tc_name: The name of the directory containing the data to be commited.
        :param commit_msg: An optional commit message. IF not set, the commit message
            will be the tc_name.

        :returns: Commit action.
        """
        return self.group.initial_commit(tc_name, commit_msg)

    def wait(self, wait_time_s: float) -> tf.WaitAction:
        """
        Adds a wait action.

        :param wait_time_s: The time to wait in seconds.

        :returns: Wait action.
        """
        return self.group.wait(wait_time_s)

    def wait_report(self, commit: tf.CommitAction | None = None) -> tf.WaitReportAction:
        """
        Adds a wait for report action.
        This action waits unitl the test system published a report for a commit.
        If no commit parameter is specified, the previous commit is used.

        :param commit: Optional commit of whose report is to be waited for.

        :returns: Wait report action
        """
        return self.group.wait_report(commit)

    def verify(self, report: tf.WaitReportAction | None = None) -> tf.VerifyAction:
        """
        Adds a verification action.
        This action checks if a report fulfills the expected results.
        If no report parameter is specified, the previous report is used.
        The results for a commit and its expected report are configured in the
        result.json file in the test case directory data/test_cases.

        :param report: Optional report to be verified.

        :returns: Verify action.
        """
        return self.group.verify(report)

    def verify_no_report(self, commit: tf.CommitAction) -> tf.VerifyNoReportAction:
        """
        Adds a verification action that will assert that no report
        is published for a specific test case.

        :param commit: Commit for which a report should not exist.

        :returns: Verify no report action.
        """
        return self.group.verify_no_report(commit)

    def verify_any_report(self) -> tf.VerifyNoReportAction:
        """
        Adds a verification action that will assert that no report
        is published.

        :returns: Verify no report action.
        """
        return self.group.verify_any_report()
