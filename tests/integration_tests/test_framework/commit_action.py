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
import logging
import traceback
import distutils.dir_util
import testsystem.filesystem as fs
import test_framework as tf
import test_framework.repository as repository
import test_framework.parsing as parsing

from .action import Action


class CommitAction(Action):
    """
    Action to create a new commit. The new commit is based on the data of a test case
    found in the data/test_cases subdirectory of the integration tests directory.
    The directory structure should look as follows:

    .. code-block::

        /                                           : Reporitory root directory
        └── tests/integration_tests/data/test_cases : Directory that contains test cases
            └── <tc_name>                           : A specific test case
                ├── data                            : This repository usually contains an
                |   ├── [apps]                      :   RTOS implementation but could include
                |   ├── [middleware]                :   anything a group should commit.
                |   └── ...                         :
                └── result.json                     : The expected results of this test case.

    The result.json file should be a JSON object of type
    :py:class:`~test_framework.parsing.ExpectedResult`.

    :param tc_name: The name of the test case directory containing the data
        to be commited.
    :param commit_msg: The commit message for the new commit.
    """

    def __init__(self, tc_name: str, commit_msg: str | None = None) -> None:
        self.tc_path = os.path.join(repository.data_src_path, "test_cases", tc_name)
        self.src_dir = os.path.join(self.tc_path, "data")
        assert os.path.exists(
            self.src_dir
        ), f"Data for commit {tc_name} does not exist. (Path: {self.src_dir})"
        assert not os.path.exists(os.path.join(self.src_dir, ".git")), (
            "Test case must not be a git repository. Delete directory .git in test"
            f" case '{tc_name}'."
        )
        self.tc_name = tc_name
        self.commit_msg = commit_msg
        self.commit_hash: str | None = None

        self.expected_result: parsing.ExpectedResult | None
        result_file = os.path.join(self.tc_path, "result.json")
        if os.path.exists(result_file):
            with open(result_file, "r") as f:
                result_content = f.read()
                self.expected_result = parsing.parse_expected_results(result_content)

    def run(self):
        primary_branch = self.group.test_system.get_config("git_primary_branch_name")
        repo = self.group.repo
        repo.git.checkout(primary_branch)
        distutils.dir_util.copy_tree(self.src_dir, repo.working_dir)  # type: ignore
        if fs._git_changed(repo):
            commit_msg = self.commit_msg
            if commit_msg is None:
                commit_msg = self.tc_name
            repo.git.add("*")
            repo.git.commit(m=commit_msg)
            self.commit_hash = repo.head.commit.hexsha
            repo.git.push()


class InitialCommitAction(CommitAction):
    """
    Action to create a new commit that gets pushed immediately.
    This guarantees that the commit is already present when the test system starts.

    :param tc_name: The name of the test case directory containing the data
        to be commited.
    :param commit_msg: The message of the commit.
    """

    def __init__(
        self, tc_name: str, group: tf.GroupModel, commit_msg: str | None = None
    ) -> None:
        super().__init__(tc_name, commit_msg)
        super().set_group(group)
        try:
            super().run()
        except:
            traceback.print_exc()
            logging.error("[TEST] Initial commit action failed.")

    def run(self):
        pass
