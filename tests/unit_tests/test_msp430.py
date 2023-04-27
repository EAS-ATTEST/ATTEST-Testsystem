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

import pytest
import unittest.mock as mock

import testsystem.models.msp430 as msp

from sqlalchemy.orm import Session
from db_fixtures import *


def test_create_msp430(db_session):
    serial_number = "2E1F896E1C0002FF"
    m, created = msp.get_or_create(db_session, serial_number)
    assert m is not None
    assert created
    assert m.id > 0
    assert m.serial_number == serial_number


def test_get_msp430(db_session: Session):
    serial_number = "2E1F896E1C0002FF"
    m1 = (
        db_session.query(msp.MSP430)
        .where(msp.MSP430.serial_number == serial_number)
        .first()
    )
    m2, created2 = msp.get_or_create(db_session, serial_number)
    m3, created3 = msp.get_or_create(db_session, serial_number)
    assert m1 is None
    assert m2 is not None
    assert created2
    assert m2 is m3
    assert not created3


@mock.patch("testsystem.models.msp430.serial.Serial")
@mock.patch("testsystem.models.msp430.comports")
def test_successfully_connected(m_comports, m_serial, db_session: Session):
    serial_number = "2E1F896E1C000200"

    port1 = mock.MagicMock()
    port1.serial_number = serial_number
    port1.device = "/dev/ttyACM98"
    port1.interface = "MSP Debug Interface"

    port2 = mock.MagicMock()
    port2.serial_number = serial_number
    port2.device = "/dev/ttyACM99"
    port2.interface = "MSP Application UART"

    m_comports.return_value = [port1, port2]

    connected = msp.is_connected(db_session, serial_number)
    m, created = msp.get_or_create(db_session, serial_number)

    assert connected
    assert not created
    assert m.debug_port == port1.device
    assert m.uart_port == port2.device


@mock.patch("testsystem.models.msp430.serial.Serial")
@mock.patch("testsystem.models.msp430.comports")
def test_is_not_connected_if_only_debug_port_available(
    m_comports, m_serial, db_session: Session
):
    serial_number = "2E1F896E1C000200"

    port = mock.MagicMock()
    port.serial_number = serial_number
    port.device = "/dev/ttyACM98"
    port.interface = "MSP Debug Interface"

    m_comports.return_value = [port]

    connected = msp.is_connected(db_session, serial_number)

    assert not connected


@mock.patch("testsystem.models.msp430.serial.Serial")
@mock.patch("testsystem.models.msp430.comports")
def test_is_not_connected_if_only_uart_port_available(m_comports, db_session: Session):
    serial_number = "2E1F896E1C000200"

    port = mock.MagicMock()
    port.serial_number = serial_number
    port.device = "/dev/ttyACM98"
    port.interface = "MSP Application UART"

    m_comports.return_value = [port]

    connected = msp.is_connected(db_session, serial_number)

    assert not connected


@mock.patch("testsystem.models.msp430.utils.run_external_task")
@mock.patch("testsystem.models.msp430.comports")
def test_update_ports_if_disconnected(m_comports, m_serial, db_session: Session):
    serial_number = "2E1F896E1C000200"

    port1 = mock.MagicMock()
    port1.serial_number = serial_number
    port1.device = "/dev/ttyACM98"
    port1.interface = "MSP Debug Interface"

    port2 = mock.MagicMock()
    port2.serial_number = serial_number
    port2.device = "/dev/ttyACM99"
    port2.interface = "MSP Application UART"

    m_comports.side_effect = [[port1, port2], []]

    m, _ = msp.get_or_create(db_session, serial_number)
    connected = msp.is_connected(db_session, serial_number)
    m.set_defective()
    notconnected = msp.is_connected(db_session, serial_number)
    m, created = msp.get_or_create(db_session, serial_number)

    assert not created
    assert connected
    assert not notconnected
    assert m.debug_port is None
    assert m.uart_port is None


@mock.patch("testsystem.models.msp430.comports")
def test_get_connected(m_comports, db_session: Session):
    serial_number1 = "2E1F896E1C000201"
    serial_number2 = "2E1F896E1C000202"

    port1 = mock.MagicMock()
    port1.serial_number = serial_number1
    port1.device = "/dev/ttyACM98"
    port1.interface = "MSP Debug Interface"
    port1.manufacturer = "Texas Instruments"
    port1.pid = 19
    port1.product = "MSP Tools Driver"
    port1.vid = 8263

    port2 = mock.MagicMock()
    port2.serial_number = serial_number2
    port2.device = "/dev/ttyACM99"
    port2.interface = "MSP Application UART"
    port2.manufacturer = "Texas Instruments 2"
    port2.pid = 19
    port2.product = "MSP Tools Driver 2"
    port2.vid = 8263

    m_comports.return_value = [port1, port2]

    msps = msp.get_connected(db_session)

    assert len(msps) == 2

    assert msps[0].serial_number == serial_number1
    assert msps[0].debug_port == port1.device
    assert msps[0].uart_port is None
    assert msps[0].manufacturer == port1.manufacturer
    assert msps[0].pid == port1.pid
    assert msps[0].product == port1.product
    assert msps[0].vid == port1.vid

    assert msps[1].serial_number == serial_number2
    assert msps[1].debug_port is None
    assert msps[1].uart_port == port2.device
    assert msps[1].manufacturer == port2.manufacturer
    assert msps[1].pid == port2.pid
    assert msps[1].product == port2.product
    assert msps[1].vid == port2.vid


@mock.patch("testsystem.models.msp430.comports")
def test_get_only_correct_pid_and_vid_as_connected(m_comports, db_session: Session):
    port1 = mock.MagicMock()
    port1.serial_number = None
    port1.device = "/dev/ttyACM98"
    port1.interface = "MSP Debug Interface"
    port1.manufacturer = "Texas Instruments"
    port1.pid = 20
    port1.product = "MSP Tools Driver"
    port1.vid = 8263

    port2 = mock.MagicMock()
    port2.serial_number = None
    port2.device = "/dev/ttyACM98"
    port2.interface = "MSP Debug Interface"
    port2.manufacturer = "Texas Instruments"
    port2.pid = 19
    port2.product = "MSP Tools Driver"
    port2.vid = 8264

    m_comports.return_value = [port1, port2]

    msps = msp.get_connected(db_session)

    assert len(msps) == 0


def test_increment_flash_counter(db_session: Session):
    serial_number = "2E1F896E1C000200"
    msp.increment_flash_counter(db_session, serial_number)
    m, created = msp.get_or_create(db_session, serial_number)
    assert m.flash_counter == 1
    assert not created


@mock.patch("testsystem.models.msp430.comports")
def test_dont_get_connected_msp_twice(m_comports, db_session: Session):
    serial_number = "2E1F896E1C000200"

    port1 = mock.MagicMock()
    port1.serial_number = serial_number
    port1.device = "/dev/ttyACM98"
    port1.interface = "MSP Debug Interface"
    port1.manufacturer = "Texas Instruments"
    port1.product = "MSP Tools Driver"
    port1.pid = 19
    port1.vid = 8263

    port2 = mock.MagicMock()
    port2.serial_number = serial_number
    port2.device = "/dev/ttyACM99"
    port2.interface = "MSP Application UART"
    port2.manufacturer = "Texas Instruments"
    port2.product = "MSP Tools Driver"
    port2.pid = 19
    port2.vid = 8263

    m_comports.return_value = [port1, port2]

    msps1 = msp.get_connected(db_session)
    msps2 = msp.get_connected(db_session)

    assert len(msps1) == 1
    assert len(msps2) == 1
