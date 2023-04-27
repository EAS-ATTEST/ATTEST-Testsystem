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

from testsystem.config import Config
from testsystem.exceptions import ConfigError
from testsystem.models import MSP430, PicoScope, ConnectionInfo, TestUnit
from testsystem.models.test_unit import TestUnit


@mock.patch("testsystem.models.test_unit.get_config")
def test_parsing_required_connection(m_get_config):
    conf = Config()
    conf.tu_connections = ["P1.2-D3"]
    m_get_config.return_value = conf
    cons: list[ConnectionInfo] = TestUnit.get_required_connections()  # type: ignore
    assert 1 == len(cons)
    assert 1 == cons[0].msp_port
    assert 2 == cons[0].msp_pin
    assert "D3" == cons[0].pico_channel


@mock.patch("testsystem.models.test_unit.get_config")
def test_parsing_required_connection_reversed(m_get_config):
    conf = Config()
    conf.tu_connections = ["D1-P2.3"]
    m_get_config.return_value = conf
    cons: list[ConnectionInfo] = TestUnit.get_required_connections()  # type: ignore
    assert 1 == len(cons)
    assert 2 == cons[0].msp_port
    assert 3 == cons[0].msp_pin
    assert "D1" == cons[0].pico_channel


@mock.patch("testsystem.models.test_unit.get_config")
def test_parsing_multiple_required_connection(m_get_config):
    conf = Config()
    conf.tu_connections = ["P1.2-D3", "P4.5-D6"]
    m_get_config.return_value = conf
    cons: list[ConnectionInfo] = TestUnit.get_required_connections()  # type: ignore
    assert 2 == len(cons)
    assert 1 == cons[0].msp_port
    assert 2 == cons[0].msp_pin
    assert "D3" == cons[0].pico_channel
    assert 4 == cons[1].msp_port
    assert 5 == cons[1].msp_pin
    assert "D6" == cons[1].pico_channel


@pytest.mark.parametrize(
    "config_str",
    [
        "",
        "P1.1D1",
        "P1.1--D1",
        "P1.-D1",
        "P.1-D1",
        "1.1-D1",
        "P1.1-D",
        "P1.1-1",
    ],
)
@mock.patch("testsystem.models.test_unit.get_config")
def test_parsing_invalid_required_connection(m_get_config, config_str):
    conf = Config()
    conf.tu_connections = [config_str]
    m_get_config.return_value = conf
    with pytest.raises(ConfigError):
        TestUnit.get_required_connections()  # type: ignore


@mock.patch("testsystem.models.test_unit.TestUnit")
def test_test_unit_validation(m_test_unit):
    required_connections = [ConnectionInfo(1, 2, "D3")]
    m_test_unit.get_required_connections = mock.MagicMock(
        return_value=required_connections
    )
    msp = MSP430()
    picoscope = PicoScope()
    connections = [ConnectionInfo(1, 2, "D3", msp=msp, pico=picoscope)]
    valid, cons = TestUnit.validate_setup(msp, picoscope, connections)
    assert True == valid
    assert 1 == len(cons)
    assert connections[0] == cons[0]


@mock.patch("testsystem.models.test_unit.TestUnit")
def test_test_unit_validation_with_missing_connection(m_test_unit):
    required_connections = [ConnectionInfo(1, 2, "D4")]
    m_test_unit.get_required_connections = mock.MagicMock(
        return_value=required_connections
    )
    msp = MSP430()
    picoscope = PicoScope()
    connections = [ConnectionInfo(1, 2, "D3", msp=msp, pico=picoscope)]
    valid, cons = TestUnit.validate_setup(msp, picoscope, connections)
    assert False == valid
    assert 0 == len(cons)


@mock.patch("testsystem.models.test_unit.TestUnit")
def test_test_unit_validation_with_multiple_connection(m_test_unit):
    required_connections = [ConnectionInfo(1, 2, "D3")]
    m_test_unit.get_required_connections = mock.MagicMock(
        return_value=required_connections
    )
    msp = MSP430()
    picoscope = PicoScope()
    connections = [
        ConnectionInfo(1, 1, "D2", msp=msp, pico=picoscope),
        ConnectionInfo(1, 2, "D3", msp=msp, pico=picoscope),
    ]
    valid, cons = TestUnit.validate_setup(msp, picoscope, connections)
    assert True == valid
    assert 1 == len(cons)
    assert connections[1] == cons[0]


@mock.patch("testsystem.models.test_unit.TestUnit")
def test_test_unit_validation_with_multiple_required_connection(m_test_unit):
    required_connections = [ConnectionInfo(1, 1, "D1"), ConnectionInfo(1, 2, "D2")]
    m_test_unit.get_required_connections = mock.MagicMock(
        return_value=required_connections
    )
    msp = MSP430()
    picoscope = PicoScope()
    connections = [
        ConnectionInfo(1, 1, "D1", msp=msp, pico=picoscope),
        ConnectionInfo(1, 2, "D2", msp=msp, pico=picoscope),
    ]
    valid, cons = TestUnit.validate_setup(msp, picoscope, connections)
    assert True == valid
    assert 2 == len(cons)
    assert connections[0] == cons[0]
    assert connections[1] == cons[1]


@mock.patch("testsystem.models.test_unit.TestUnit")
def test_test_unit_validation_with_wrong_msp(m_test_unit):
    required_connections = [ConnectionInfo(1, 1, "D1")]
    m_test_unit.get_required_connections = mock.MagicMock(
        return_value=required_connections
    )
    msp1 = MSP430()
    msp2 = MSP430()
    picoscope = PicoScope()
    connections = [ConnectionInfo(1, 2, "D3", msp=msp1, pico=picoscope)]
    valid, cons = TestUnit.validate_setup(msp2, picoscope, connections)
    assert False == valid
    assert 0 == len(cons)


@mock.patch("testsystem.models.test_unit.TestUnit")
def test_test_unit_validation_with_wrong_picoscope(m_test_unit):
    required_connections = [ConnectionInfo(1, 1, "D1")]
    m_test_unit.get_required_connections = mock.MagicMock(
        return_value=required_connections
    )
    msp = MSP430()
    picoscope1 = PicoScope()
    picoscope2 = PicoScope()
    connections = [ConnectionInfo(1, 2, "D3", msp=msp, pico=picoscope1)]
    valid, cons = TestUnit.validate_setup(msp, picoscope2, connections)
    assert False == valid
    assert 0 == len(cons)
