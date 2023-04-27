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
import pytest
import unittest.mock as mock
import numpy as np

from testsystem.models import ChannelReader, PicoReader


def test_capturing_streamed_data():
    handle = None
    no_of_samples = 16
    start_idx = 0
    overflow = 0
    trigger_at = 0
    triggered = 0
    auto_stop = 0

    m_pico_reader = mock.MagicMock()
    m_pico_reader_ptr = ctypes.cast(
        ctypes.pointer(ctypes.py_object(m_pico_reader)), ctypes.c_void_p
    )
    m_pico_reader._PicoReader__reading = True
    channel_reader = [ChannelReader(i, 1) for i in range(16)]
    m_pico_reader._PicoReader__channel_reader = channel_reader
    # Pin 0 & Pin 1 valid data; others not connected
    port_0_data = np.array([3, 2, 3, 3, 0, 2, 3, 1, 2, 3, 3, 3, 3, 3, 3, 3])
    m_pico_reader._PicoReader__port_0_buffer = port_0_data
    # Pin 8 invalid & Pin 11 valid; others not connected
    port_1_data = np.array([9, 9, 1, 1, 9, 1, 1, 9, 1, 1, 0, 8, 8, 8, 8, 8])
    m_pico_reader._PicoReader__port_1_buffer = port_1_data

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

    assert 0xB3 == channel_reader[0].get_data()[0]
    assert 0xFB == channel_reader[1].get_data()[0]
    assert 0x12 == channel_reader[11].get_data()[0]
    for i in range(2, 16):
        if i != 11:
            assert 0 == len(channel_reader[i].get_data())
