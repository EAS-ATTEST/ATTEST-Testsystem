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
import time
import logging
import threading
import random
import numpy as np
import testsystem.config as cnf
import testsystem.filesystem as fs
import testsystem.reporting as reporting
import testsystem.models.test_set as testset
import testsystem.models.task_worker as task_worker


from testsystem.models import Task, Group, TestCaseDef, TestCase, TestSet, TestCaseTask
from testsystem.exceptions import MSPConnectionError, GitError, ProcessError
from testsystem.constants import (
    SCHEDULER_PAUSE_S,
    TUTAG_SCOPE,
    LEGACY_TASK_PRIO,
    FORCE_TEST_TAG_PRIO,
)

_scheduled_tasks: list[Task] = []
_scheduled_tasks_lock = threading.Lock()

_schedule_stop_event = threading.Event()
_scheduling_thread: threading.Thread | None = None

_last_prio_reset_timestamp = 0

_poll_interval_s: int | None = None


def poll_interval() -> int | None:
    global _poll_interval_s
    return _poll_interval_s


class TestRun:
    __test__ = False

    def __init__(
        self, tc_defs: list[TestCaseDef], test_set: TestSet, test_env: fs.TestEnv
    ):
        self.tc_defs = tc_defs
        self.test_set = test_set
        self.test_env = test_env
        self.finished_tcs: list[TestCase] = []
        self.lock = threading.Lock()

    @property
    def group_name(self) -> str:
        return self.test_set.group.group_name

    @property
    def finished(self) -> bool:
        if self.test_set is None:
            return False
        return self.test_set.finished

    @property
    def commit(self) -> str:
        return self.test_set.commit_hash

    def get_tasks(self, priority: float | None = None) -> list[Task]:
        if priority is None:
            priority = self.test_set.group.get_priority()
        assert priority is not None
        tasks = []
        for tc_def in self.tc_defs:
            tu_tag = None
            if tc_def.timing:
                tu_tag = TUTAG_SCOPE
            task = TestCaseTask(
                self.test_set.group,
                priority,
                tc_def,
                self.test_env,
                test_unit_tag=tu_tag,
                callback=self.test_finished,
                error_callback=self.test_failed,
            )
            tasks.append(task)
        return tasks

    def task_finished(self, test_case: TestCase):
        with self.lock:
            self.finished_tcs.append(test_case)
            tc_finished_cnt = len(self.finished_tcs)
            logging.info(
                f"Test run for group {self.group_name} completed {tc_finished_cnt} out"
                f" of {len(self.tc_defs)} tests (Commit={self.commit[0:8]})."
            )
            test_case.timestamp = int(time.time() * 1000)
            self.test_set = testset.add_result(self.test_set, test_case.result)

        if tc_finished_cnt == len(self.tc_defs):
            self.__test_run_finished()

    def test_finished(self, test_case_task: TestCaseTask):
        tc = test_case_task.test_case
        success_status = "SUCCESS"
        if not tc.successful:
            success_status = "FAILED"
        logging.debug(
            f"Test case {tc.definition.name} for group {tc.group_name} finished after"
            f" {np.round(test_case_task.runtime, 3)}s. Status: {success_status}"
        )
        self.task_finished(tc)

    def test_failed(self, test_case_task: TestCaseTask, err: Exception):
        test_case_task.test_unit.msp430.set_defective()  # type: ignore
        test_case_task.priority = 9
        tc = test_case_task.test_case
        logging.error(
            (
                f"Test case {tc.definition.name} for group {tc.group_name} failed after"
                f" {np.round(test_case_task.runtime, 3)}s. Reschedule {test_case_task}."
            ),
            exc_info=err,
        )
        schedule_task(test_case_task)

    def __test_run_finished(self):
        try:
            self.test_set.set_finished()
            md_test_report = reporting.create_md_report_for_test_set(self.test_set)
            md_group_report = reporting.create_md_group_report(test_set=self.test_set)
            fs.publish_test_run_report(self.group_name, self.commit, md_test_report)
            fs.publish_group_report(self.group_name, self.commit, md_group_report)
            fs.publish_system_status_report(reporting.create_md_system_report())
        except Exception as ex:
            logging.error(
                f"Finishing test run for group {self.group_name} and commit"
                f" {self.commit[0:8]} failed. {ex}"
            )
            # Delete test set to restart a test run for this commit
            self.test_set.delete()
        finally:
            self.test_env.cleanup()


def _handle_priority_reset(groups: list[Group]):
    global _last_prio_reset_timestamp
    config = cnf.get_config()
    timestamp = time.time()
    last_reset_delta = timestamp - _last_prio_reset_timestamp
    prio_valid_s = config.prio_reset_h * 3600
    if last_reset_delta >= prio_valid_s:
        logging.info(f"Start priority reset.")
        global _scheduled_tasks, _scheduled_tasks_lock
        with _scheduled_tasks_lock:
            logging.info(
                f"Set all {len(_scheduled_tasks)} remaining tasks in queue to priority"
                f" {LEGACY_TASK_PRIO}."
            )
            for task in _scheduled_tasks:
                task.priority = LEGACY_TASK_PRIO
        _last_prio_reset_timestamp = timestamp
        logging.info(f"Reset group priorities to default.")
        for group in groups:
            group.reset_queue_time()
        logging.info(f"Priority reset finished.")


def _setup_tasks(
    group: Group, commit: str, tc_defs: list[TestCaseDef], priority: float | None = None
) -> list[Task]:
    test_env = fs.setup_test_env(group.group_name, commit)
    assert test_env.commit_hash == commit
    logging.info(
        f"Setup test case tasks for group {group.group_name} and commit {commit[0:8]}."
    )
    test_set = TestSet.get_or_create(group.id, test_env.commit_hash)
    test_set.update(test_env.commit_time, test_env.commit_msg)
    test_run = TestRun(tc_defs, test_set, test_env)
    return test_run.get_tasks(priority)


def _check_group_for_new_tasks(group: Group, tc_defs: list[TestCaseDef]) -> list[Task]:
    group_name = group.group_name
    try:
        fs.load_group(group_name)
        latest_test_set = group.get_latest_test_set()
        latest_commit = None
        if latest_test_set is not None:
            if not latest_test_set.finished:
                return []
            latest_commit = latest_test_set.commit_hash
        next_commit = fs.get_latest_commit(group_name)
        if next_commit != latest_commit and not TestSet.exists(group.id, next_commit):
            lc_hash = "None" if latest_commit is None else latest_commit[0:8]
            logging.info(
                f"Found new commit {next_commit[0:8]} for group {group_name}. Latest"
                f" tested commit is {lc_hash}."
            )
            return _setup_tasks(group, next_commit, tc_defs)
    except GitError as ex:
        logging.warning(f"Failed to load new tasks for group {group_name}. {ex.msg}")
    return []


def _check_group_for_forced_tasks(
    group: Group, tc_defs: list[TestCaseDef], tags: list[str]
) -> list[Task]:
    group_name = group.group_name
    tasks: list[Task] = []
    try:
        fs.load_group(group_name)
        tagged_commits = fs.get_tagged_group_commit(group_name, tags)
        for tagged_commit in tagged_commits:
            if not TestSet.exists(group.id, tagged_commit):
                logging.info(
                    f"Found untested tagged commit {tagged_commit[0:8]} for group"
                    f" {group_name}."
                )
                tasks.extend(
                    _setup_tasks(
                        group, tagged_commit, tc_defs, priority=FORCE_TEST_TAG_PRIO
                    )
                )
    except GitError as ex:
        logging.warning(f"Failed to load new tasks for group {group_name}. {ex.msg}")
    return tasks


def _run_scheduling(stop_event: threading.Event):
    logging.info("[SCHEDULER] Started successful.")
    while not stop_event.is_set():
        try:
            start_time = time.time()
            conf = cnf.get_config()
            groups = Group.get_by_term(conf.term)
            _handle_priority_reset(groups)
            tc_defs = TestCaseDef.get()
            try:
                fs.load_public()
            except GitError as ex:
                logging.error(f"Loading public repo failed. {ex.msg}")
                break
            random.shuffle(groups)
            for group in groups:
                tasks = _check_group_for_new_tasks(group, tc_defs)
                tasks.extend(
                    _check_group_for_forced_tasks(group, tc_defs, conf.force_test_tags)
                )
                if len(tasks) > 0:
                    task_cnt = 0
                    for t in tasks:
                        task_cnt = schedule_task(t)
                    logging.info(
                        f"[SCHEDULER] Added {len(tasks)} new tasks for"
                        f" {group.group_name}. There are currently {task_cnt} tasks"
                        " queued."
                    )
                    time.sleep(SCHEDULER_PAUSE_S)
            time.sleep(SCHEDULER_PAUSE_S)
            global _poll_interval_s
            _poll_interval_s = int(time.time() - start_time)
            logging.debug(
                f"[SCHEDULER] Group check finished. Poll interval: {_poll_interval_s}s"
            )
        except Exception as ex:
            logging.error(f"[SCHEDULER] Unhandled error occurred.", exc_info=ex)
            time.sleep(SCHEDULER_PAUSE_S)
    logging.info("[SCHEDULER] Stopped successful.")


def start():
    """
    Starts the scheduling thread.
    """
    global _scheduling_thread, _schedule_stop_event
    assert _scheduling_thread is None
    logging.info("[SCHEDULER] Starting...")
    _schedule_stop_event.clear()
    _scheduling_thread = threading.Thread(
        target=_run_scheduling, args=(_schedule_stop_event,)
    )
    _scheduling_thread.start()


def stop():
    """
    Stops the scheduling thread. This call blocks until the scheduler stopped.
    """
    global _scheduling_thread, _schedule_stop_event
    assert _scheduling_thread is not None
    logging.info("[SCHEDULER] Stopping...")
    _schedule_stop_event.set()
    _scheduling_thread.join()


def schedule_task(task: Task) -> int:
    """
    Add a new task the the queue.

    :param task: The task to schedule.

    :returns: Returns the current new size of the queue.
    """
    global _scheduled_tasks, _scheduled_tasks_lock
    with _scheduled_tasks_lock:
        task.schedule_time = time.time()
        added = False
        for i in range(len(_scheduled_tasks)):
            if _scheduled_tasks[i].priority > task.priority:
                _scheduled_tasks.insert(i, task)
                added = True
                break
            else:
                assert (
                    _scheduled_tasks[i].priority <= task.priority
                ), "Scheduled tasks list must be ordered at any time."
        if not added:
            _scheduled_tasks.append(task)
        queue_len = len(_scheduled_tasks)
    logging.debug(f"Schedule {task}. There are currently {queue_len} tasks queued.")
    return queue_len


def get_next_task(worker: task_worker.TaskWorker) -> Task | None:
    """
    Get the next task from the schedule queue. If a task is returned it is also removed
    from the queue.

    :param worker: The worker which will run the task.

    :returns: Returns the next task in queue for the specific task worker or None if
        nothing is to be done.
    """
    global _scheduled_tasks, _scheduled_tasks_lock
    with _scheduled_tasks_lock:
        next_task: Task | None = None
        for i in range(len(_scheduled_tasks)):
            task = _scheduled_tasks[i]
            if task.use_specific_test_unit:
                if task.specific_test_unit == worker.test_unit:
                    next_task = task
            elif task.use_tagged_test_unit:
                if worker.test_unit.has_tag(task.test_unit_tag):
                    next_task = task
            else:
                next_task = task

            if next_task is not None:
                break

        if next_task is not None:
            _scheduled_tasks.remove(next_task)
            logging.info(
                f"[SCHEDULER] Assign {next_task} to {worker}. There are"
                f" {len(_scheduled_tasks)} remaining tasks in queue."
            )

        return next_task


def queue_size() -> int:
    """
    Get the current queue size. The result is not guaranteed to be still valid when read
    by the caller.

    :returns: Queue length.
    """
    global _scheduled_tasks_lock, _scheduled_tasks
    with _scheduled_tasks_lock:
        return len(_scheduled_tasks)
