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
import os
import shutil
import logging
import numpy as np
import testsystem as ts

import test_framework.repository as repository
import test_framework.config as config
import test_framework.db as db
import test_framework.group_model as group_model


def setup_test_system(
    name: str = "unnamed", exercise_nr: int = 1, keep_repos: bool = False
) -> TestSystemModel:
    """
    Setup a test system model for a specif test case.

    :param name: An arbitrary name for the test environemt. You could use the name of
        the testcase.
    :param exercise_nr: The exercise number which the test system should use.
    :param kee_repos: Flag to disable deletion of repos when the test case finished.

    :returns: A test system model instance. Use its register_group() method to add
        groups.
    """
    return TestSystemModel(name, exercise_nr, keep_repos)


class TestSystemModel:
    """
    Setup a test system model for a specif test case.

    :param name: An arbitrary name for the test environemt. You could use the name of
        the testcase.
    :param exercise_nr: The exercise number which the test system should use.
    :param kee_repos: Flag to disable deletion of repos when the test case finished.
    """

    __test__ = False

    def __init__(
        self,
        name: str = "unnamed",
        exercise_nr: int = 1,
        keep_repos: bool = False,
    ) -> None:
        self.name = name
        self.keep_repos = keep_repos
        self.working_dir = os.path.join(os.getcwd(), f"__{name}")
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)
        self.git_remote = os.path.join(self.working_dir, "__git_remote")
        self.git_local = os.path.join(self.working_dir, "__git_local")
        self.groups: list[group_model.GroupModel] = []
        self.group_nrs: list[int] = []

        self.config_file = config.setup_config(self.working_dir)
        self.set_config("git_server", self.git_remote)
        self.set_config("exercise_nr", exercise_nr)
        self.set_config("log_file", os.path.join(self.working_dir, f"{name}.log"))

        self.db_engine, self.db_file = db.setup_db(self.working_dir)
        self.set_config("db_file", self.db_file)

        self.sys_repo = repository.setup_test_repo(self, "Testsystem_Reports")
        self.public_repo = repository.setup_test_repo(self, "RTOS_Public_SS00")

    def __del__(self):
        if not self.keep_repos:
            repository.delete_test_repo(self, "RTOS_Public_SS00")
            repository.delete_test_repo(self, "Testsystem_Reports")
        db.delete_db(self.db_engine, self.db_file)
        config.delete_config(self.config_file)

    def register_group(self, group_nr: int) -> group_model.GroupModel:
        """
        Register a group on the test system model. The test system will test the commits
        made by this group.

        :param group_nr: The group number.

        :returns: A newly registered group model. Use its convenience methods to add
            actions for the group.
        """
        grp = group_model.GroupModel(group_nr, self)
        self.group_nrs.append(group_nr)
        self.groups.append(grp)
        self.set_config("group_ids", self.group_nrs)
        return grp

    def run(self):
        """
        Start and run the test system and execute group actions. This call blocks until
        the test system is shut down.
        """
        for group in self.groups:
            group.start()
        start_time = time.time()
        ts.run()
        runtime = time.time() - start_time
        errors = []
        for group in self.groups:
            group.stop()
            for err in group.errors:
                errors.append(err)
        logging.info(f"[TEST] Test case runtime: {np.round(runtime, 0)}s")
        if len(errors) == 0:
            logging.info(f"[TEST] SUCCESSFUL")
        else:
            logging.info(f"[TEST] FAILED")
            err_msgs = ""
            for err in errors:
                err_msgs += err + "\n"
            assert (
                False
            ), f"{err_msgs}\nTest case '{self.name}' failed with {len(errors)} errors."

    def set_config(
        self,
        property: str,
        value: str | int | bool | list[str] | list[int] | list[bool],
    ):
        """
        Update a config property for the test system.

        :param property: The name of the property.
        :param value: The new value for the property.
        """
        config.set_config(self.config_file, property, value)

    def get_config(self, property: str) -> str:
        """
        Get the value of a specific config property.

        :param property: The property name from which to get the value.

        :returns: Returns the property value as string.
        """
        return config.get_config(property)
