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

import ctypes
import unittest.mock as mock
import numpy as np

from testsystem.models import ChannelReader, PicoReader


def test_stop_reading_on_auto_stop():
    handle = None
    no_of_samples = 0
    start_idx = 0
    overflow = 0
    trigger_at = 0
    triggered = 0
    auto_stop = 1

    m_pico_reader = mock.MagicMock()
    m_pico_reader_ptr = ctypes.cast(
        ctypes.pointer(ctypes.py_object(m_pico_reader)), ctypes.c_void_p
    )
    m_pico_reader._PicoReader__reading = True
    m_pico_reader._PicoReader__channel_reader = [ChannelReader(i, 1) for i in range(16)]

    PicoReader._PicoReader__streaming_callback(  # type: ignore
        handle,
        no_of_samples,
        start_idx,
        overflow,
        trigger_at,
        triggered,
        auto_stop,
        m_pico_reader_ptr,
    )

    assert False == m_pico_reader._PicoReader__reading


def test_pin_reader_with_single_byte():
    r = ChannelReader(0, 1)
    r.record([1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    data = r.get_data()
    assert 1 == len(data)
    assert 0xC3 == data[0]


def test_pin_reader_with_consecutive_records():
    r = ChannelReader(0, 1)
    r.record([1, 0, 1, 1, 0, 0])
    r.record([0, 0, 1, 1, 1, 1, 1])
    data = r.get_data()
    assert 1 == len(data)
    assert 0xC3 == data[0]


def test_pin_reader_with_multiple_bytes():
    r = ChannelReader(0, 1)
    signal = np.concatenate(
        (
            [1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
        )
    )
    r.record(signal)
    data = r.get_data()
    assert 2 == len(data)
    assert 0x0F == data[0]
    assert 0x80 == data[1]


def test_read_invalid_uart_signal():
    r = ChannelReader(0, 1)
    r.record([1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1])
    assert 0 == len(r.get_data())
