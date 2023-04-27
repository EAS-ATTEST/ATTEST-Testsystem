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

import threading
import testsystem as ts

import test_framework as tf
import test_framework.repository as repository

from .action import Action
from .commit_action import CommitAction, InitialCommitAction
from .wait_action import WaitAction, WaitReportAction
from .verify_action import VerifyAction, VerifyNoReportAction
from .stop_testsystem_action import StopTestsystemAction


class GroupModel:
    """
    A model to simulate a group's behavior and verify the results returned by the test
    system.
    A group model starts with an initial git repository equal to the one provided by
    the contents of ``tests/integration_tests/git/RTOS_SS00_GroupInit.tar.gz``.
    The model then performs some actions based on its configuration.

    :param group_nr: An arbitrary group number.
    :param test_system: The test system model where to register this group.
    """

    def __init__(self, group_nr: int, test_system: tf.TestSystemModel) -> None:
        self.__thread = None
        self.__stop_event = threading.Event()
        self.__actions: list[Action] = []
        self.__last_commit: CommitAction | None = None
        self.__last_report: WaitReportAction | None = None
        self.__sealed: bool = False

        self.test_system = test_system

        self.group_name = ts.Group.get_name(group_nr, "SS00")
        self.repo = repository.setup_empty_group_repo(test_system, self.group_name)
        self.errors = []

    def add_action(self, action: Action):
        """
        Add an action to the group model. Once the model is started, it performs the
        actions in the order in which they were added.

        :param action: The action to add.
        """
        assert (
            self.__thread is None
        ), "You may not add actions once the group is started."
        assert not self.__sealed, (
            "You may not add actions after a stop testsystem action. They are not"
            " guaranteed to be executed."
        )
        action.set_group(self)
        self.__actions.append(action)
        if isinstance(action, CommitAction):
            self.__last_commit = action
        if isinstance(action, WaitReportAction):
            self.__last_report = action
        if isinstance(action, StopTestsystemAction):
            self.__sealed = True

    @property
    def successful(self) -> bool:
        assert self.__thread is None, "Stop the group first."
        return len(self.errors) == 0

    def start(self):
        """
        Starts the group model.
        """
        if self.__thread is not None:
            return
        self.__stop_event.clear()
        self.__thread = threading.Thread(target=self.__run)
        self.__thread.start()

    def stop(self):
        """
        Stops the group model.
        """
        assert self.__thread is not None, "Group model is not started."
        self.__stop_event.set()
        self.__thread.join()
        self.__thread = None

    def __run(self):
        for action in self.__actions:
            if self.__stop_event.is_set():
                break
            action.run_save()

    def stop_test_system(self) -> StopTestsystemAction:
        """
        Adds an action to stop and shutdown the test system.
        You may not add actions after a stop testsystem action.
        They are not guaranteed to be executed.
        """
        action = StopTestsystemAction()
        self.add_action(action)
        return action

    def commit(self, tc_name: str, commit_msg: str | None = None) -> CommitAction:
        """
        Adds a commit action. The data to commit is specified by the parameter tc_name,
        which is the name of a directory in data/test_cases.

        :param tc_name: The name of the directory containing the data to be commited.
        :param commit_msg: An optional commit message. IF not set, the commit message
            will be the tc_name.

        :returns: Commit action.
        """
        action = CommitAction(tc_name, commit_msg)
        self.add_action(action)
        return action

    def initial_commit(
        self, tc_name: str, commit_msg: str | None = None
    ) -> InitialCommitAction:
        """
        Adds a commit that is already present when the test system starts. The data to
        commit is specified by the parameter tc_name, which is the name of a directory
        in data/test_cases.

        :param tc_name: The name of the directory containing the data to be commited.
        :param commit_msg: An optional commit message. IF not set, the commit message
            will be the tc_name.

        :returns: Commit action.
        """
        action = InitialCommitAction(tc_name, self, commit_msg)
        self.add_action(action)
        return action

    def wait(self, wait_time_s: float) -> WaitAction:
        """
        Adds a wait action.

        :param wait_time_s: The time to wait in seconds.

        :returns: Wait action.
        """
        action = WaitAction(wait_time_s)
        self.add_action(action)
        return action

    def wait_report(self, commit: CommitAction | None = None) -> WaitReportAction:
        """
        Adds a wait for report action. This action waits unitl the test system
        published a report for a commit. If no commit parameter is specified, the
        previous commit is used.

        :param commit: Optional commit of whose report is to be waited for.

        :returns: Wait report action
        """
        if commit is None:
            assert self.__last_commit is not None
            commit = self.__last_commit
        action = WaitReportAction(commit, self.__stop_event)
        self.add_action(action)
        return action

    def verify(self, report: WaitReportAction | None = None) -> VerifyAction:
        """
        Adds a verification action. This action checks if a report fulfills the
        expected results. If no report parameter is specified, the previous report is
        used. The results for a commit and its expected report are configured in the
        result.json file in the test case directory data/test_cases.

        :param report: Optional report to be verified.

        :returns: Verify action.
        """
        if report is None:
            assert self.__last_report is not None
            report = self.__last_report
        action = VerifyAction(report)
        self.add_action(action)
        return action

    def verify_no_report(self, commit: CommitAction) -> VerifyNoReportAction:
        """
        Adds an action that will verify that no report is published for a specific test
        case.

        :param commit: Commit for which a report should not exist.

        :returns: Verify no report action.
        """
        action = VerifyNoReportAction(commit)
        self.add_action(action)
        return action

    def verify_any_report(self) -> VerifyNoReportAction:
        """
        Adds an action that will verify that no report is published.

        :returns: Verify no report action.
        """
        action = VerifyNoReportAction()
        self.add_action(action)
        return action
