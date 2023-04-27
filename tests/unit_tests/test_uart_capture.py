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

from testsystem.models.uart_capture import UARTCapture, _read_uart_byte
from testsystem.exceptions import StartBitError, StopBitError


@pytest.mark.parametrize(
    "conf",
    [
        ([1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1], 1, 0x0F, 11),
        (
            [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1],
            2,
            0x55,
            21,
        ),
    ],
)
def test_read_uart_byte(conf):
    byte, consumed_len = _read_uart_byte(conf[0], conf[1])  # type: ignore
    assert conf[2] == byte
    assert conf[3] == consumed_len


def test_full_consumption_of_uart_signal():
    signal = [1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1]
    byte, consumed_len = _read_uart_byte(signal, 1)  # type: ignore
    assert 0b10100101 == byte
    assert 15 == consumed_len


def test_ignore_too_short_uart_signal():
    signal = [0, 1, 1, 1, 1, 0, 0, 0, 0]
    byte, consumed_len = _read_uart_byte(signal, 1)  # type: ignore
    assert None == byte
    assert 9 == consumed_len


def test_next_uart_without_a_signal():
    signal = [1 for _ in range(15)]
    byte, consumed_len = _read_uart_byte(signal, 1)  # type: ignore
    assert None == byte
    assert 15 == consumed_len


def test_starbit_error():
    signal = np.concatenate(([0], [1 for _ in range(2 + 9 * 3)]))
    with pytest.raises(StartBitError):
        _read_uart_byte(signal, 3)  # type: ignore


def test_stopbit_error():
    signal = [0 for _ in range(10)]
    with pytest.raises(StopBitError):
        _read_uart_byte(signal, 1)  # type: ignore


def test_uart_capture_class():
    c = UARTCapture(1)
    assert False == c.complete
    assert 5 == c.capture([0, 1, 1, 0, 0])
    assert False == c.complete
    assert 7 == c.capture([0, 0, 1, 1, 1, 1, 1, 1, 1])
    assert True == c.complete
    assert 0xC3 == c.get_byte()


def test_uart_capture_with_delayed_start_bit():
    c = UARTCapture(1)
    signal = np.concatenate(
        ([1 for _ in range(100)], [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1])
    )
    assert len(signal) == c.capture(signal)
    assert True == c.is_valid()
    assert 0x55 == c.get_byte()


def test_uart_capture_with_correct_start_index():
    c = UARTCapture(1)
    assert 6 == c.capture([1, 0, 1, 1, 1, 1])
    assert 7 == c.capture([1, 1, 1, 0, 1, 1, 1])
    assert True == c.is_valid()
    assert 0x7F == c.get_byte()
