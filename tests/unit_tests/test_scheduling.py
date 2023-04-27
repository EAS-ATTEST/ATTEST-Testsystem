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
import unittest.mock as mock

from testsystem.scheduling import get_next_task, schedule_task, TestRun
from testsystem.models import Task
from testsystem.constants import TUTAG_SCOPE


def test_schedule_task_once():
    test_unit = mock.MagicMock()
    task1 = Task()
    schedule_task(task1)

    first_task = get_next_task(test_unit)
    second_task = get_next_task(test_unit)

    assert task1 == first_task
    assert None == second_task


def test_schedule_task_with_correct_priority():
    test_unit = mock.MagicMock()
    task1 = Task(priority=1)
    task2 = Task(priority=2)
    task3 = Task(priority=3)
    schedule_task(task2)
    schedule_task(task1)
    schedule_task(task3)

    first_task = get_next_task(test_unit)
    second_task = get_next_task(test_unit)
    third_task = get_next_task(test_unit)

    assert task1 == first_task
    assert task2 == second_task
    assert task3 == third_task


def test_schedule_task_with_equal_priority():
    test_unit = mock.MagicMock()
    task1 = Task(priority=1)
    task2 = Task(priority=1)
    schedule_task(task1)
    schedule_task(task2)

    first_task = get_next_task(test_unit)
    second_task = get_next_task(test_unit)

    assert task1 == first_task
    assert task2 == second_task


def test_schedule_task_for_special_test_unit():
    test_unit1 = mock.MagicMock()
    test_unit2 = mock.MagicMock()
    task_worker1 = mock.MagicMock()
    task_worker1.test_unit = test_unit1
    task_worker2 = mock.MagicMock()
    task_worker2.test_unit = test_unit2
    task1 = Task(priority=1, test_unit=test_unit1)
    task2 = Task(priority=2, test_unit=test_unit2)
    task3 = Task(priority=3)
    task4 = Task(priority=3)
    schedule_task(task4)
    schedule_task(task3)
    schedule_task(task1)
    schedule_task(task2)

    first_tu2 = get_next_task(task_worker2)
    first_tu1 = get_next_task(task_worker1)
    second_tu2 = get_next_task(task_worker2)
    second_tu1 = get_next_task(task_worker1)

    assert task2 == first_tu2
    assert task1 == first_tu1
    assert task4 == second_tu2
    assert task3 == second_tu1


def test_schedule_task_on_tagged_test_unit():
    def has_t1(tag):
        return tag == "t1"

    def has_t2(tag):
        return tag == "t2"

    test_unit1 = mock.MagicMock()
    test_unit2 = mock.MagicMock()
    task_worker1 = mock.MagicMock()
    task_worker1.test_unit = test_unit1
    task_worker1.test_unit.has_tag = has_t1
    task_worker2 = mock.MagicMock()
    task_worker2.test_unit = test_unit2
    task_worker2.test_unit.has_tag = has_t2
    task1 = Task(priority=1, tag="t1")
    task2 = Task(priority=2, tag="t2")
    task3 = Task(priority=3)
    task4 = Task(priority=3)
    schedule_task(task4)
    schedule_task(task3)
    schedule_task(task1)
    schedule_task(task2)

    first_tu2 = get_next_task(task_worker2)
    first_tu1 = get_next_task(task_worker1)
    second_tu2 = get_next_task(task_worker2)
    second_tu1 = get_next_task(task_worker1)

    assert task2 == first_tu2
    assert task1 == first_tu1
    assert task4 == second_tu2
    assert task3 == second_tu1


def test_get_tasks():
    tc1 = mock.MagicMock()
    tc1.timing = True
    tc2 = mock.MagicMock()
    tc2.timing = False
    group = mock.MagicMock()
    group.get_priority.returns = 10
    test_set = mock.MagicMock()
    test_set.group = group
    test_env = mock.MagicMock()
    test_run = TestRun([tc1, tc2], test_set, test_env)

    tasks = test_run.get_tasks()

    assert 2 == len(tasks)
    assert TUTAG_SCOPE == tasks[0].test_unit_tag
    assert None == tasks[1].test_unit_tag
