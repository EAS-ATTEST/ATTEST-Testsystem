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

import time
import sys
import unittest.mock as mock
import testsystem.models.test_set as ts

from testsystem.models import Group, TestResult, TestSet
from db_fixtures import *


@mock.patch("testsystem.models.test_set.db")
def test_add_results(m_db, db_engine):
    # Arrange
    m_db.get_engine = mock.Mock(return_value=db_engine)
    connection = db_engine.connect()
    with Session(bind=connection, expire_on_commit=False) as session:
        session.begin(subtransactions=True)
        group = Group(group_name="Test_Group", group_nr=999, term="SS0")
        session.add(group)
        session.flush()
        test_set = ts._get_or_create(session, group.id, "CAFE")
        test_result = TestResult(successful=True, timestamp=time.time(), test_case_id=0)

        # Act
        test_set = ts.add_result(test_set, test_result)

        # Assert
        db_test_results = (
            session.query(TestResult)
            .filter(TestResult.test_set_id == test_set.id)
            .all()
        )
        assert 1 == len(db_test_results)
        assert test_result.id > 0
        assert test_result in test_set.test_results
        assert test_set.group.id == group.id  # must be loaded

        session.rollback()


@pytest.mark.parametrize(
    "msg",
    [
        {"input": "Commit message", "expected": "Commit message"},
        {"input": "Commit message\n", "expected": "Commit message"},
        {"input": "  Commit message  ", "expected": "Commit message"},
        {"input": "\"'/\\<>[](){}?#|", "expected": "???????????????"},
        {"input": "ABXYabxy190 :-.!", "expected": "ABXYabxy190 :-.!"},
    ],
)
@mock.patch("testsystem.models.test_set.db")
def test_commit_message_format(m_db, db_engine, msg):
    # Arrange
    m_db.get_engine = mock.Mock(return_value=db_engine)
    with Session(bind=db_engine, expire_on_commit=False) as session:
        session.begin(subtransactions=True)
        group = Group(group_name="test_commit_message_format", group_nr=998, term="SS0")
        session.add(group)
        session.flush()
        test_set = ts._get_or_create(session, group.id, "CAFE")

        # Act
        ts._update(session, test_set.id, 0, msg["input"])
        obj_msg = test_set.commit_message
        db_msg = session.get(TestSet, test_set.id).commit_message

        # Assert
        assert msg["expected"] == obj_msg
        assert msg["expected"] == db_msg
        session.rollback()
