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

import git
import os
import time
import threading
import testsystem.constants as const
import test_framework.parsing as parsing

from .action import Action
from .commit_action import CommitAction


class WaitAction(Action):
    def __init__(self, wait_time_s: float):
        self.wait_time_s = wait_time_s

    def run(self):
        time.sleep(self.wait_time_s)


class WaitReportAction(Action):
    def __init__(self, commit: CommitAction, stop_event: threading.Event | None = None):
        self.report: parsing.DetailedGroupResult | None = None
        self.commit_action = commit
        if stop_event is None:
            self.__stop_event = threading.Event()
        else:
            self.__stop_event = stop_event

    def run(self):
        assert self.commit_action is not None
        assert self.commit_action.commit_hash is not None
        while not self.__stop_event.is_set():
            try:
                repo = self.group.repo
                repo.git.fetch()
                repo.git.checkout(const.GIT_RESULT_BRANCH_NAME)
                repo.git.pull()
                commit_list = list(repo.iter_commits(reverse=True))
                for c in commit_list:
                    repo.git.checkout(c.hexsha)
                    report_path = os.path.join(repo.working_dir, "reports", "README.md")  # type: ignore
                    if not os.path.exists(report_path):
                        continue
                    with open(report_path, "r") as f:
                        content = f.read()
                    result = parsing.parse_group_report(content)
                    if (
                        result is not None
                        and result.tested_commit[0:8]
                        == self.commit_action.commit_hash[0:8]
                    ):
                        self.report = result
                        return
            except git.GitCommandError:
                pass
            time.sleep(1)
