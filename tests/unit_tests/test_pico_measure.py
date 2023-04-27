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

import time
import pytest
import ctypes
import unittest.mock as mock
import numpy as np

from testsystem.models.pico_measure import PicoMeasure, _measure_timing
from testsystem.constants import TEST_TIMING_CLK_DEVIDER


def test_measure_timing():
    data = [0, 1, 0]
    trigger_at = 0

    cnt = _measure_timing(data, trigger_at, search_increment=1)  # type: ignore

    assert 1 == cnt


def test_measure_timing_without_signal():
    data = [0, 0, 0, 0]
    trigger_at = 0

    cnt = _measure_timing(data, trigger_at, search_increment=1)  # type: ignore

    assert 0 == cnt


def test_measure_timing_with_trigger_offset():
    data = [0, 0, 0, 1, 1, 0]
    trigger_at = 1

    cnt = _measure_timing(data, trigger_at, search_increment=1)  # type: ignore

    assert 2 == cnt


def test_measure_timing_ignores_other_digital_channels_on_trigger():
    data = [0xFE, 0xFF, 0xFF, 0xFE]
    trigger_at = 1

    cnt = _measure_timing(data, trigger_at, search_increment=1)  # type: ignore

    assert 2 == cnt


def test_measure_timing_ignores_other_digital_channels():
    data = [0xAE, 0xA7, 0xBB, 0xCD, 0xFE]
    trigger_at = 0

    cnt = _measure_timing(data, trigger_at, search_increment=1)  # type: ignore

    assert 3 == cnt


def test_measure_timing_with_quick_search():
    data = [0, 1, 1, 1, 0, 0, 0]
    trigger_at = 0

    cnt = _measure_timing(data, trigger_at, search_increment=2)  # type: ignore

    assert 3 == cnt


def test_measure_timing_with_quick_search_on_small_buffer():
    data = [0, 1, 0]
    trigger_at = 0

    cnt = _measure_timing(data, trigger_at, search_increment=3)  # type: ignore

    assert 1 == cnt


def test_measure_timing_without_end():
    data = [0, 1, 1]
    trigger_at = 0

    with pytest.raises(TimeoutError):
        _measure_timing(data, trigger_at, search_increment=1)  # type: ignore


def test_measure_timing_effect_with_quick_search():
    trigger_at = 1000003
    sig_len = 7000003
    data = np.concatenate(
        [np.zeros(trigger_at + 10), np.ones(sig_len), np.zeros(1000033)]
    )

    start_1 = time.time()
    cnt_1 = _measure_timing(data, trigger_at, search_increment=1)  # type: ignore
    start_2 = time.time()
    cnt_2 = _measure_timing(data, trigger_at, search_increment=1009)  # type: ignore
    end = time.time()

    assert cnt_1 == sig_len
    assert cnt_2 == sig_len

    delta_1 = start_2 - start_1
    delta_2 = end - start_2
    speedup = delta_1 / delta_2
    assert 200 <= speedup
    assert 2000 >= speedup


def test_measure_timing_on_different_channel():
    channel_nr = 7
    trigger_at = 1
    signal_end = 21
    expected_cnt = signal_end - trigger_at
    data = np.zeros(100)
    for i in range(trigger_at, signal_end):
        data[i] = 1 << channel_nr

    cnt = _measure_timing(data, trigger_at, search_increment=10, chnl_mask=(1 << channel_nr))  # type: ignore

    assert expected_cnt == cnt


@mock.patch("testsystem.models.pico_measure.PICO_CLOCK_SAMPLING_NS", 1000000)
@mock.patch("testsystem.models.pico_measure.TestUnit.get_timing_channel")
@mock.patch("testsystem.models.pico_measure.ps")
def test_measure_timing_on_port0(m_ps, m_get_timing_channel):
    # Arrange
    channel_nr = 7
    signal_value = 1 << channel_nr
    m_get_timing_channel.return_value = channel_nr
    m_pico_scope = mock.MagicMock()

    chnl_dict = {}
    for i in range(0, 16):
        chnl_dict[f"PS2000A_DIGITAL_CHANNEL_{i}"] = i
    m_ps.PS2000A_DIGITAL_CHANNEL = chnl_dict
    m_ps.PS2000A_DIGITAL_PORT = {
        "PS2000A_DIGITAL_PORT0": "Port0",
        "PS2000A_DIGITAL_PORT1": "Port1",
    }
    m_ps.PS2000A_TRIGGER_STATE = {
        "PS2000A_CONDITION_DONT_CARE": 0,
        "PS2000A_CONDITION_TRUE": 1,
    }
    m_ps.ps2000aOpenUnit.return_value = 0
    m_ps.ps2000aCloseUnit.return_value = 0
    m_ps.ps2000aSetDigitalPort.return_value = 0
    m_ps.ps2000aSetChannel.return_value = 0
    m_ps.ps2000aSetDataBuffer.return_value = 0
    m_ps.ps2000aSetTriggerChannelConditions.return_value = 0
    m_ps.ps2000aSetTriggerDigitalPortProperties.return_value = 0
    m_ps.ps2000aStop.return_value = 0
    m_ps.ps2000aRunStreaming.return_value = 0

    pico_measure = PicoMeasure(m_pico_scope)
    sample_time_ns = pico_measure._PicoMeasure__sample_time_ns  # type: ignore
    no_of_samples = pico_measure._PicoMeasure__buffer_len  # type: ignore
    trigger_at = int(100)
    signal_end = int(2100)
    expected_time = (
        (signal_end - trigger_at) * sample_time_ns / (TEST_TIMING_CLK_DEVIDER * 1000)
    )

    def streaming_callback(handle, c_func_ptr, pico_measure_ptr) -> int:
        start_idx = 0
        overflow = 0
        triggered = 1
        auto_stop = 0
        for i in range(0, no_of_samples):
            if i >= trigger_at and i < signal_end:
                pico_measure._PicoMeasure__port_buffer[i] = signal_value  # type: ignore
            else:
                pico_measure._PicoMeasure__port_buffer[i] = 0  # type: ignore
        pico_measure._PicoMeasure__streaming_callback(  # type: ignore
            handle,
            no_of_samples,
            start_idx,
            overflow,
            trigger_at,
            triggered,
            auto_stop,
            pico_measure_ptr,
        )
        return 0

    m_ps.ps2000aGetStreamingLatestValues = streaming_callback

    # Act
    pico_measure.lock()
    pico_measure.start()
    result = pico_measure.measure()
    pico_measure.unlock()

    # Assert
    assert expected_time == result

    set_port_calls = m_ps.ps2000aSetDigitalPort.mock_calls
    port0_enabled = False
    for call in set_port_calls:
        if call.args[2] == 1:
            assert "Port0" == call.args[1]
            port0_enabled = True
    assert port0_enabled

    trigger_chnl_cond_calls = m_ps.ps2000aSetTriggerChannelConditions.mock_calls
    assert 1 == len(trigger_chnl_cond_calls)
    trigger_chnl_cond = trigger_chnl_cond_calls[0].args[1]._obj
    assert 0 == trigger_chnl_cond.channelA
    assert 0 == trigger_chnl_cond.channelB
    assert 0 == trigger_chnl_cond.channelC
    assert 0 == trigger_chnl_cond.channelD
    assert 0 == trigger_chnl_cond.external
    assert 0 == trigger_chnl_cond.aux
    assert 0 == trigger_chnl_cond.pulseWidthQualifier
    assert 1 == trigger_chnl_cond.digital

    trigger_port_prop_calls = m_ps.ps2000aSetTriggerDigitalPortProperties.mock_calls
    assert 1 == len(trigger_port_prop_calls)
    trigger_port_prop = trigger_port_prop_calls[0].args[1]._obj
    assert channel_nr == trigger_port_prop.channel
    assert 1 == trigger_port_prop.direction
    assert True


@mock.patch("testsystem.models.pico_measure.PICO_CLOCK_SAMPLING_NS", 1000000)
@mock.patch("testsystem.models.pico_measure.TestUnit.get_timing_channel")
@mock.patch("testsystem.models.pico_measure.ps")
def test_measure_timing_on_port1(m_ps, m_get_timing_channel):
    # Arrange
    channel_nr = 8
    signal_value = 1 << (channel_nr - 8)
    m_get_timing_channel.return_value = channel_nr
    m_pico_scope = mock.MagicMock()

    chnl_dict = {}
    for i in range(0, 16):
        chnl_dict[f"PS2000A_DIGITAL_CHANNEL_{i}"] = i
    m_ps.PS2000A_DIGITAL_CHANNEL = chnl_dict
    m_ps.PS2000A_DIGITAL_PORT = {
        "PS2000A_DIGITAL_PORT0": "Port0",
        "PS2000A_DIGITAL_PORT1": "Port1",
    }
    m_ps.PS2000A_TRIGGER_STATE = {
        "PS2000A_CONDITION_DONT_CARE": 0,
        "PS2000A_CONDITION_TRUE": 1,
    }
    m_ps.ps2000aOpenUnit.return_value = 0
    m_ps.ps2000aCloseUnit.return_value = 0
    m_ps.ps2000aSetDigitalPort.return_value = 0
    m_ps.ps2000aSetChannel.return_value = 0
    m_ps.ps2000aSetDataBuffer.return_value = 0
    m_ps.ps2000aSetTriggerChannelConditions.return_value = 0
    m_ps.ps2000aSetTriggerDigitalPortProperties.return_value = 0
    m_ps.ps2000aStop.return_value = 0
    m_ps.ps2000aRunStreaming.return_value = 0

    pico_measure = PicoMeasure(m_pico_scope)
    sample_time_ns = pico_measure._PicoMeasure__sample_time_ns  # type: ignore
    no_of_samples = pico_measure._PicoMeasure__buffer_len  # type: ignore
    trigger_at = int(100)
    signal_end = int(2100)
    expected_time = (
        (signal_end - trigger_at) * sample_time_ns / (TEST_TIMING_CLK_DEVIDER * 1000)
    )

    def streaming_callback(handle, c_func_ptr, pico_measure_ptr) -> int:
        start_idx = 0
        overflow = 0
        triggered = 1
        auto_stop = 0
        for i in range(0, no_of_samples):
            if i >= trigger_at and i < signal_end:
                pico_measure._PicoMeasure__port_buffer[i] = signal_value  # type: ignore
            else:
                pico_measure._PicoMeasure__port_buffer[i] = 0  # type: ignore
        pico_measure._PicoMeasure__streaming_callback(  # type: ignore
            handle,
            no_of_samples,
            start_idx,
            overflow,
            trigger_at,
            triggered,
            auto_stop,
            pico_measure_ptr,
        )
        return 0

    m_ps.ps2000aGetStreamingLatestValues = streaming_callback

    # Act
    pico_measure.lock()
    pico_measure.start()
    result = pico_measure.measure()
    pico_measure.unlock()

    # Assert
    assert expected_time == result

    set_port_calls = m_ps.ps2000aSetDigitalPort.mock_calls
    port1_enabled = False
    for call in set_port_calls:
        if call.args[2] == 1:
            assert "Port1" == call.args[1]
            port1_enabled = True
    assert port1_enabled

    trigger_chnl_cond_calls = m_ps.ps2000aSetTriggerChannelConditions.mock_calls
    assert 1 == len(trigger_chnl_cond_calls)
    trigger_chnl_cond = trigger_chnl_cond_calls[0].args[1]._obj
    assert 0 == trigger_chnl_cond.channelA
    assert 0 == trigger_chnl_cond.channelB
    assert 0 == trigger_chnl_cond.channelC
    assert 0 == trigger_chnl_cond.channelD
    assert 0 == trigger_chnl_cond.external
    assert 0 == trigger_chnl_cond.aux
    assert 0 == trigger_chnl_cond.pulseWidthQualifier
    assert 1 == trigger_chnl_cond.digital

    trigger_port_prop_calls = m_ps.ps2000aSetTriggerDigitalPortProperties.mock_calls
    assert 1 == len(trigger_port_prop_calls)
    trigger_port_prop = trigger_port_prop_calls[0].args[1]._obj
    assert channel_nr == trigger_port_prop.channel
    assert 1 == trigger_port_prop.direction
    assert True
