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
import numpy as np
import unittest.mock as mock

from testsystem.exceptions import DecodeError
from testsystem.models.connection_detector import (
    _generate_id,
    _decode_msp_info,
)


def test_id_generation():
    start_pattern = 0xFE
    device_id = _generate_id(start_pattern)  # type: ignore
    assert start_pattern == (device_id >> 24) & 0xFF
    assert 0 != device_id & 0xFFFFFF


@mock.patch("testsystem.models.connection_detector.get_uuid")
def test_id_part_does_not_contain_start_pattern(m_get_uuid):
    start_pattern = 0xFE
    m_get_uuid.side_effect = [0xFE1234, 0x12FE34, 0x1234FE, 0x56789A]
    device_id = _generate_id(start_pattern)  # type: ignore
    assert start_pattern == (device_id >> 24) & 0xFF
    assert 0 != device_id & 0x56789A


def test_decode_id_data():
    start_pattern = 0xFE
    data = [0xFE, 0xAA, 0xBB, 0xCC, 0x12]
    device_id, port, pin = _decode_msp_info(data, start_pattern)  # type: ignore
    assert 0xFEAABBCC == device_id
    assert 1 == port
    assert 2 == pin


def test_decode_id_data_with_offset():
    start_pattern = 0xFE
    data = [0x00, 0x00, 0xFE, 0xAA, 0xBB, 0xCC, 0x12]
    device_id, port, pin = _decode_msp_info(data, start_pattern)  # type: ignore
    assert 0xFEAABBCC == device_id
    assert 1 == port
    assert 2 == pin


def test_decode_id_data_multiple_records():
    start_pattern = 0xFE
    data = [0xFE, 0xAA, 0xBB, 0xCC, 0x12, 0xFE, 0xAA, 0xBB, 0xCC, 0x12]
    device_id, port, pin = _decode_msp_info(data, start_pattern)  # type: ignore
    assert 0xFEAABBCC == device_id
    assert 1 == port
    assert 2 == pin


def test_decode_id_data_multiple_records_and_offset():
    start_pattern = 0xFE
    data = np.concatenate(
        (
            [0x00, 0xFE, 0xAA, 0xBB, 0xCC, 0x12],
            [0x00, 0x00, 0xFE, 0xAA, 0xBB, 0xCC, 0x12],
        )
    )
    device_id, port, pin = _decode_msp_info(data, start_pattern)  # type: ignore
    assert 0xFEAABBCC == device_id
    assert 1 == port
    assert 2 == pin


def test_decode_id_fails_with_to_little_data():
    start_pattern = 0xFE
    data = [0xFE, 0xAA, 0xBB, 0xCC]
    with pytest.raises(DecodeError):
        _decode_msp_info(data, start_pattern)  # type: ignore


def test_decode_id_fails_with_inconsistent_id():
    start_pattern = 0xFE
    data = np.concatenate(
        (
            [0xFE, 0xAA, 0xBB, 0xCC, 0x12],
            [0xFE, 0xA1, 0xBB, 0xCC, 0x12],
        )
    )
    with pytest.raises(DecodeError):
        _decode_msp_info(data, start_pattern)  # type: ignore


def test_decode_id_fails_with_inconsistent_port():
    start_pattern = 0xFE
    data = np.concatenate(
        (
            [0xFE, 0xAA, 0xBB, 0xCC, 0x12],
            [0xFE, 0xAA, 0xBB, 0xCC, 0x22],
        )
    )
    with pytest.raises(DecodeError):
        _decode_msp_info(data, start_pattern)  # type: ignore


def test_decode_id_fails_with_inconsistent_pin():
    start_pattern = 0xFE
    data = np.concatenate(
        (
            [0xFE, 0xAA, 0xBB, 0xCC, 0x12],
            [0xFE, 0xAA, 0xBB, 0xCC, 0x13],
        )
    )
    with pytest.raises(DecodeError):
        _decode_msp_info(data, start_pattern)  # type: ignore
