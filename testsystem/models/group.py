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

import testsystem.db as db

from sqlalchemy import (
    select,
    Column,
    Integer,
    TIMESTAMP,
    Boolean,
    String,
    Float,
    desc,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Session, relationship, joinedload

from testsystem.config import get_config
from .test_set import TestSet


class Group(db.Base):
    """
    The group class. This class is also a database object.
    """

    __tablename__ = "Groups"

    id: int = Column(Integer, primary_key=True)  # type: ignore
    group_nr: int = Column(Integer, nullable=False)  # type: ignore
    group_name: str = Column(String(50), nullable=False, unique=True)  # type: ignore
    term: str = Column(String(4), nullable=False)  # type: ignore
    active: bool = Column(Boolean, nullable=False, default=False)  # type: ignore
    creation_time = Column(TIMESTAMP, server_default=func.now())
    abs_queue_time: float = Column(Float, nullable=False, default=0)  # type: ignore
    queue_time: float = Column(Float, nullable=False, default=0)  # type: ignore

    test_set_results = relationship(
        "TestSet",
        order_by=desc(TestSet.commit_time),
        back_populates="group",
    )

    @classmethod
    def get(cls, group_nr: int, term: str) -> Group | None:
        """
        Get a specific group by its number and the term.

        :param group_nr: The group number.
        :param term: The term. E.g: SS22

        :returns: The group if it exists, ``None`` otherwise.
        """
        _init_and_update_groups(term)
        with Session(db.get_engine(), expire_on_commit=False) as session:
            group = (
                session.query(cls)
                .filter(cls.group_nr == group_nr)
                .filter(cls.term == term)
                .first()
            )
            return group

    @classmethod
    def get_by_id(cls, id: int) -> Group | None:
        """
        Get a group by its id.

        :param id: The group id.

        :returns: The group if it exists, ``None`` otherwise.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return session.get(Group, id)

    @classmethod
    def get_by_term(cls, term: str, active=True) -> list[Group]:
        """
        Get all groups from a specific term.

        :param term: The term. E.g: SS22

        :returns: Returns a list of groups.
        """
        _init_and_update_groups(term)
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return list(
                session.query(cls).where(cls.term == term).where(cls.active == active)
            )

    @classmethod
    def get_name(cls, group_nr, term) -> str:
        """
        Returns the group name based on the group number and term.
        Use this method every time you need to construct the group name from the group
        number.

        :param group_nr: The group number.
        :param term: The term. E.g: SS22

        :returns: The group name. E.g: RTOS_SS22_Group01
        """
        return f"RTOS_{term}_Group{str(group_nr).zfill(2)}"

    def get_test_set(self, commit) -> TestSet | None:
        """
        Get a specific test set from this group.

        :returns: The test set if it exists, ``None`` otherwise.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            test_set = (
                session.query(TestSet)
                .options(joinedload(TestSet.test_results))
                .filter(TestSet.group_id == self.id)
                .filter(TestSet.commit_hash == commit)
                .first()
            )
            return test_set  # type: ignore

    def get_latest_test_set(self) -> TestSet | None:
        """
        Get the latest test set for this group.

        :returns: The latest test set if it exists, ``None`` otherwise.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            test_set = (
                session.query(TestSet)
                .options(joinedload(TestSet.test_results))
                .filter(TestSet.group_id == self.id)
                .order_by(desc(TestSet.id), desc(TestSet.commit_time))
                .first()
            )
            return test_set  # type: ignore

    def get_latest_finished_test_set(self) -> TestSet | None:
        """
        Get the latest test set which is already finished for this group.

        :returns: The latest finished test set if it exists, ``None`` otherwise.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            test_set = (
                session.query(TestSet)
                .options(joinedload(TestSet.test_results))
                .filter(TestSet.group_id == self.id)
                .filter(TestSet.finished == True)
                .order_by(desc(TestSet.commit_time))
                .first()
            )
            return test_set  # type: ignore

    @staticmethod
    def get_max_queue_time() -> float:
        """
        Get the max queue time of all groups.

        :returns: The max queue time in seconds.
        """
        with Session(db.get_engine()) as session:
            return session.query(func.max(Group.queue_time)).one()[0]  # type: ignore

    def get_queue_time(self) -> float:
        """
        Get the queue time of the group.

        :returns: The queue time in seconds.
        """
        with Session(db.get_engine()) as session:
            group = session.get(Group, self.id)
            self.queue_time = group.queue_time
            return group.queue_time

    def add_queue_time(self, waiting_time: float):
        """
        Add time to this groups queue time.

        :param waiting_time: The time to add in seconds.
        """
        with Session(db.get_engine()) as session:
            group = session.get(Group, self.id)
            group.queue_time += waiting_time
            group.abs_queue_time += waiting_time
            self.queue_time = group.queue_time
            self.abs_queue_time = group.abs_queue_time
            session.commit()

    def get_priority(self) -> float:
        """
        Get the priority of this group.
        Change this method if you want to modify the group priority calculation.
        The priority is between 10 and 20 to leave some levels for higher priority
        tasks that may come in the future.

        :returns: The priority of this group.
        """
        max_queue_time = Group.get_max_queue_time()
        priority = 10
        if max_queue_time > 0:
            prio_factor = self.get_queue_time() / max_queue_time
            priority = 10 + prio_factor * 10  # Use priority between 10 and 20
        if priority < 10:
            priority = 10
        if priority > 20:
            priority = 20
        return priority

    def reset_queue_time(self):
        """
        Reset this groups queue time to zero.
        """
        with Session(db.get_engine()) as session:
            group = session.get(Group, self.id)
            group.queue_time = 0
            self.queue_time = 0
            session.commit()


def _init_and_update_groups(term: str):
    with Session(db.get_engine()) as session:
        # Deactivate all
        sel_stmt = select(Group).where(Group.active == True)
        for group in session.scalars(sel_stmt):
            group.active = False
        session.flush()

        # Activate configured groups
        conf = get_config()
        for nr in conf.group_ids:
            group = (
                session.query(Group)
                .where(Group.group_nr == nr)
                .where(Group.term == term)
                .first()
            )
            # If group does not exist, create it
            if group is None:
                group_name = Group.get_name(nr, term)
                group = Group(
                    group_nr=nr, group_name=group_name, term=term, active=True
                )
                session.add(group)
            # If group does exist, activate it
            else:
                group.active = True
            session.flush()
        session.commit()
