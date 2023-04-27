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

import logging
import time
import string
import testsystem.db as db

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Session, relationship, joinedload

from .test_result import TestResult


def _update(
    session: Session, test_set_id: int, commit_time: int, commit_msg: str | None = None
):
    ascii = string.ascii_letters
    digits = string.digits
    special_letters = "üöäÜÖÄß"
    special_chars = ":-.! "
    char_white_list = ascii + digits + special_letters + special_chars

    result = session.get(TestSet, test_set_id)
    result.commit_time = commit_time
    if commit_msg is not None:
        commit_msg = commit_msg.strip().split("\n")[0]
        formatted_msg = "".join(
            [c if c in char_white_list else "?" for c in commit_msg]
        )
        result.commit_message = formatted_msg[0:50]


def _delete_unfinished_test_sets(session: Session):
    sets = session.query(TestSet).filter(TestSet.finished == False).all()
    logging.debug(f"Delete {len(sets)} unfinished test sets.")
    for set in sets:
        session.delete(set)
    session.commit()


def _delete_test_set(session: Session, test_set: TestSet):
    set = session.get(TestSet, test_set.id)
    session.delete(set)
    session.commit()


def _get_or_create(session: Session, group_id: int, commit_hash: str) -> TestSet:
    qry = (
        session.query(TestSet)
        .filter(TestSet.commit_hash == commit_hash)
        .options(joinedload(TestSet.test_results))
        .options(joinedload(TestSet.group))
    )
    set_result = qry.first()
    if set_result is None:
        set_result = TestSet(
            group_id=group_id,
            commit_hash=commit_hash,
            timestamp=(time.time() * 1000),
        )
        session.add(set_result)
        session.commit()
        set_result = qry.first()
    return set_result  # type: ignore


def _add_result(session: Session, test_set_id: int, test_result: TestResult):
    _ts: TestSet = session.get(TestSet, test_set_id)
    _ts.test_results.append(test_result)
    session.commit()


def add_result(test_set: TestSet, test_result: TestResult) -> TestSet:
    """
    Add a new test result to this test set.

    :param test_set: The test set where to add the new result.
    :param test_result: The test result which should be added.

    :returns: Returns the updated test set.
    """
    with Session(db.get_engine(), expire_on_commit=False) as session:
        _add_result(session, test_set.id, test_result)
        qry = (
            session.query(TestSet)
            .filter(TestSet.id == test_set.id)
            .options(joinedload("group"))
        )
        return qry.first()  # type: ignore


def delete_unfinished_test_sets():
    """
    Delete all unfinished test sets.
    This should only be used during start-up and never be called during regular test
    system operation.
    """
    with Session(db.get_engine()) as session:
        _delete_unfinished_test_sets(session)


class TestSet(db.Base):
    """
    Data container for a test run and collection of test results.
    This is also a database object.
    """

    __test__ = False

    __tablename__ = "TestSets"

    id: int = Column(Integer, primary_key=True)  # type: ignore
    group_id: int = Column(Integer, ForeignKey("Groups.id"), nullable=False)  # type: ignore
    commit_hash: str = Column(String(40), nullable=False, unique=True)  # type: ignore
    commit_message: str = Column(String(50), nullable=True)  # type: ignore
    commit_time: int = Column(Integer, nullable=True)  # type: ignore
    finished: bool = Column(Boolean, nullable=False, default=False)  # type: ignore
    timestamp: int = Column(Integer, nullable=False)  # type: ignore

    test_results: list[TestResult] = relationship(
        "TestResult",
        cascade="all,delete",
        order_by=TestResult.test_case_id,
        back_populates="test_set_result",
    )
    group = relationship("Group", back_populates="test_set_results")

    @classmethod
    def get_or_create(cls, group_id: int, commit_hash: str) -> TestSet:
        """
        Get or create a test set.
        If a test set for this group and commit already exists, it will be returned.
        Otherwise, a new instance is created.

        :param group_id: The group for which this set should hold results.
        :param commit_hash: The commit hash for which this set should hold results.

        :returns: A test set instance.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return _get_or_create(session, group_id, commit_hash)

    @classmethod
    def exists(cls, group_id: int, commit_hash: str) -> bool:
        """
        Checks if a test set exists for a specific commit.

        :param group_id: The group to check for the test set.
        :param commit_hash: The commit to check for an existing test set.

        :returns: True if a test set exists and false otherwise.
        """
        with Session(db.get_engine()) as session:
            test_set = (
                session.query(TestSet)
                .filter(
                    TestSet.commit_hash == commit_hash, TestSet.group_id == group_id
                )
                .first()
            )
            return test_set is not None

    @classmethod
    def delete_unfinished_test_sets(cls):
        """
        Delete all unfinished test sets.
        This should only be used during start-up and never be called during regular test
        system operation.
        """
        logging.info("Cleanup old test sets.")
        delete_unfinished_test_sets()

    def update(self, commit_time: int, commit_msg: str | None = None):
        """
        Update this test set with additional information.

        :param commit_time: The timestamp of the commit in unix millis.
        :param commit_msg: The message of the commit used in this set.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            _update(session, self.id, commit_time, commit_msg)
            session.commit()

    def delete(self):
        """
        Delete this test set.
        """
        with Session(db.get_engine()) as session:
            _delete_test_set(session, self)

    def get_results(self) -> list[TestResult]:
        """
        Get a list of all results stored in this test set.

        :returns: A list of all results.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return (
                session.query(TestResult)
                .filter(TestResult.test_set_id == self.id)
                .all()
            )

    def set_finished(self, state: bool = True):
        """
        Set the finished state of this test set.

        :param state: If True, this set is marked finished.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            set_result: TestSet = session.get(TestSet, self.id)
            set_result.finished = state
            session.commit()
            self.finished = state
