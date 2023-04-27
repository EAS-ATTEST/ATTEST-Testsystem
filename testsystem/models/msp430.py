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
import logging
import serial

import testsystem.db as db
import testsystem.utils as utils

from serial.tools.list_ports import comports
from sqlalchemy import String, Column, Integer, Boolean
from sqlalchemy.orm import Session
from testsystem.constants import (
    COM_PORT_MSP_DEBUG_IDENTIFIER,
    COM_PORT_MSP_UART_IDENTIFIER,
    COM_PORT_MSP_PID,
    COM_PORT_MSP_VID,
    MSP430_FLASHER,
)


def _set_port(msp: MSP430, com_port):
    if com_port.interface == COM_PORT_MSP_DEBUG_IDENTIFIER:
        msp.debug_port = com_port.device
    elif com_port.interface == COM_PORT_MSP_UART_IDENTIFIER:
        msp.uart_port = com_port.device
    else:
        err_msg = f"'{com_port.interface}' is not a known port for a MSP430."
        logging.warning(err_msg)


def get_or_create(session: Session, serial_number: str) -> tuple[MSP430, bool]:
    msp = session.query(MSP430).where(MSP430.serial_number == serial_number).first()
    created = False
    if msp is None:
        msp = MSP430(serial_number=serial_number)
        session.add(msp)
        session.commit()
        created = True
    return msp, created


def get_connected(session: Session) -> list[MSP430]:
    ports = comports()
    msps = []
    for port in ports:
        if port.vid != COM_PORT_MSP_VID or port.pid != COM_PORT_MSP_PID:
            continue
        msp, _ = get_or_create(session, port.serial_number)  # type: ignore
        _set_port(msp, port)
        msp.manufacturer = port.manufacturer  # type: ignore
        msp.product = port.product  # type: ignore
        msp.vid = port.vid  # type: ignore
        msp.pid = port.pid  # type: ignore
        session.flush()
        if msp not in msps:
            msps.append(msp)
    session.commit()
    return msps


def is_connected(session: Session, serial_number: str) -> bool:
    msp, _ = get_or_create(session, serial_number)
    if not msp.defective and msp.uart_port is not None and msp.debug_port is not None:
        return True

    msp.uart_port = None
    msp.debug_port = None
    ports = comports()
    connected = False
    for port in ports:
        if port.serial_number != msp.serial_number:
            continue
        _set_port(msp, port)
        if msp.uart_port is not None and msp.debug_port is not None:
            connected = True
            break

    if msp.debug_port is not None:
        msp_port = os.path.basename(msp.debug_port)
        args = [f"{MSP430_FLASHER}", "-i", f"{msp_port}"]
        try:
            utils.run_external_task(args=args, timeout=10)
        except:
            logging.warning(f"Failed to connect to {msp}.")
            connected = False

    if connected:
        msp.defective = False

    session.commit()

    return connected


def increment_flash_counter(session: Session, serial_number: str) -> int:
    msp, _ = get_or_create(session, serial_number)
    msp.flash_counter += 1
    cnt = msp.flash_counter
    session.commit()
    return cnt


class MSP430(db.Base):
    """
    Class for MSP430 boards. This class is also a database object.
    """

    __tablename__ = "MSPs"

    id: int = Column(Integer, primary_key=True)  # type: ignore
    name: str = Column(String(30), nullable=True)  # type: ignore
    flash_counter: int = Column(Integer, nullable=False, default=0)  # type: ignore
    defective: bool = Column(Boolean, nullable=False, default=False)  # type: ignore

    manufacturer: str = Column(String(50), nullable=True)  # type: ignore
    pid: int = Column(Integer, nullable=True)  # type: ignore
    product: str = Column(String(50), nullable=True)  # type: ignore
    serial_number: str = Column(String(50), nullable=False)  # type: ignore
    vid: int = Column(Integer, nullable=True)  # type: ignore

    uart_port: str | None = Column(String(30), nullable=True)  # type: ignore
    debug_port: str | None = Column(String(30), nullable=True)  # type: ignore

    @classmethod
    def get_by_sn(cls, serial_number: str) -> MSP430 | None:
        """
        Get an MSP by its serial number.

        :param serial_number: The serial number of the MSP.

        :returns: The MSP if it exists, ``None`` otherwise.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return (
                session.query(MSP430)
                .filter(MSP430.serial_number == serial_number)
                .first()
            )

    @classmethod
    def get_connected(cls) -> list[MSP430]:
        """
        Get all connected MSPs.

        :returns: A list of all connected MSPs.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return get_connected(session)

    @classmethod
    def get_all(cls) -> list[MSP430]:
        """
        Get all MSPs ever connected to the test system.

        :returns: A list of all MSPs.
        """
        with Session(db.get_engine(), expire_on_commit=False) as session:
            return session.query(MSP430).all()

    def set_name(self, name: str):
        """
        Set the name of an MSP board.
        The name parameter is only for easier identification in the system reports
        and serves no functional purpose.

        :param name: The name to set for this MSP.
        """
        with Session(db.get_engine()) as session:
            msp = session.get(MSP430, self.id)
            msp.name = name
            self.name = name
            session.commit()

    def is_connected(self) -> bool:
        """
        Check if this MSP is currently connected.

        :returns: ``True`` if it is connected, ``False`` otherwise.
        """
        with Session(db.get_engine()) as session:
            return is_connected(session, self.serial_number)  # type: ignore

    def set_defective(self):
        """
        Mark this device as defective. Defective devices are checked if they can be
        recovered.
        """
        with Session(db.get_engine()) as session:
            msp, _ = get_or_create(session, self.serial_number)
            msp.defective = True
            self.defective = True
            session.commit()

    def increment_flash_counter(self):
        """
        Increment the flash counter of this MSP.
        """
        with Session(db.get_engine()) as session:
            self.flash_counter = increment_flash_counter(session, self.serial_number)  # type: ignore

    def get_identifier(self) -> str:
        """
        Get a string representation of this MSP.

        :returns: Representative name.
        """
        return f"VID:PID:SN = {self.vid}:{self.pid}:{self.serial_number}"

    def __repr__(self):
        name = ""
        if self.name is not None:
            return f"MSP430 {self.name} ({self.get_identifier()})"
        else:
            return f"MSP430 ({self.get_identifier()})"
