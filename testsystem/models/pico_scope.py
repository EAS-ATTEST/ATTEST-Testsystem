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

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

import testsystem.db as db


class PicoScope(db.Base):
    """
    Class for PicoScopes. This class is also a database object.
    """

    __tablename__ = "PicoScopes"

    id: int = Column(Integer, primary_key=True)  # type: ignore
    name: str = Column(String(30), nullable=True)  # type: ignore
    serial_number: str = Column(String(30), unique=True)  # type: ignore

    @classmethod
    def get_by_sn(cls, serial_number: str) -> PicoScope | None:
        """
        Get a PicoScope by its serial number.

        :param serial_number: The serial number of the PicoScope.

        :returns: The PicoScope if it exists, ``None`` otherwise.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return (
                session.query(PicoScope)
                .filter(PicoScope.serial_number == serial_number)
                .first()
            )

    @classmethod
    def from_serial(cls, serial_number: str) -> PicoScope:
        """
        Get or create a new PicoScope instance base on a serial number.

        :param serial: The serial number of the PicoScope.

        :returns: A PicoScope instance.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            picoscope = (
                session.query(PicoScope)
                .where(PicoScope.serial_number == serial_number)
                .first()
            )

            if picoscope is None:
                picoscope = cls(serial_number=serial_number)
                session.add(picoscope)
            session.commit()

        return picoscope

    @classmethod
    def get_all(cls) -> list[PicoScope]:
        """
        Get all PicoScopes ever connected to the test system.

        :returns: A list of all PicoScopes.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return session.query(PicoScope).all()

    def set_name(self, name: str):
        """
        Set the name of a PicoScope.
        The name parameter is only for easier identification in the system reports
        and serves no functional purpose.

        :param name: The name to set for this PicoScope.
        """
        with Session(db.get_engine()) as session:
            msp = session.get(PicoScope, self.id)
            msp.name = name
            self.name = name
            session.commit()

    def __repr__(self):
        if self.name is not None:
            return f"PicoScope {self.name} (SN = {self.serial_number})"
        else:
            return f"PicoScope (SN = {self.serial_number})"
