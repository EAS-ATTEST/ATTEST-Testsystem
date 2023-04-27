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
import threading

import time
import logging
import ctypes
import numpy as np

from .pico_scope import PicoScope
from .test_unit import TestUnit
from testsystem.exceptions import PicoError
from testsystem.constants import (
    PICO_LOGIC_THRESHOLD_VOLTAGE,
    PICO_CLOCK_SAMPLING_NS,
    TEST_TIMING_CLK_DEVIDER,
)
from picosdk.ps2000a import (
    ps2000a as ps,
    PS2000A_TRIGGER_CONDITIONS,
    PS2000A_DIGITAL_CHANNEL_DIRECTIONS,
)

pico_lock = threading.Lock()


def pico_success(status):
    """
    Checks if a pico return status is OK.

    :raises: PicoError if status is other than OK.
    """
    if status != 0:
        raise PicoError(status)


def _measure_timing(
    buffer, trigger_index: int, search_increment: int = 1000, chnl_mask: int = 1
) -> int:
    edge_index = trigger_index
    while int(buffer[edge_index]) & chnl_mask == 0:
        edge_index += 1
        if edge_index == len(buffer):
            return 0
    logging.debug(
        f"Correct trigger index by {edge_index - trigger_index} samples. Now @"
        f" {edge_index}."
    )

    start_index = edge_index
    stop_index = edge_index
    for i in range(edge_index, len(buffer), search_increment):
        start_index = stop_index
        stop_index = i
        if int(buffer[i]) & chnl_mask == 0:
            break

    if len(buffer) - stop_index <= search_increment:
        stop_index = len(buffer)

    time_cnt = start_index - edge_index
    for i in range(start_index, stop_index):
        if int(buffer[i]) & chnl_mask > 0:
            time_cnt += 1
        else:
            break

    if time_cnt + edge_index == len(buffer):
        raise TimeoutError()

    return time_cnt


class PicoMeasure:
    """
    Class used for timing tests to measure the timing signal on a PicoScope.

    :param picoscope: PicoScope to be used for measuring.
    """

    def __init__(self, picoscope: PicoScope):
        assert picoscope.serial_number.startswith("IU"), (
            "PicoMeasure only supports type 2000A PicoScope models. Are you sure that"
            f" {picoscope} is a 2000A model? If yes, update this assert to allow serial"
            f" numbers starting with '{picoscope[0:2]}'."
        )
        self.picoscope = picoscope
        self.timing_chnl = TestUnit.get_timing_channel()
        self.timing_chnl_mask = 1 << (self.timing_chnl - 8 * int(self.timing_chnl / 8))

        self.__logic_level = int(PICO_LOGIC_THRESHOLD_VOLTAGE / 5 * 32767)
        self.__sample_time_ns = PICO_CLOCK_SAMPLING_NS
        self.__handle = None
        self.__started = False
        self.__reading = False
        self.__trigger_index = 0
        self.__sample_cnt = 0
        self.__timing_measure_count = 0
        self.__actual_sample_int_ns = 0
        self.__buffer_len = int(10 * np.power(10, 9) / self.__sample_time_ns)  # ~ 10s
        self.__port_buffer = None

        self.__ps_measure_channel = ps.PS2000A_DIGITAL_CHANNEL[f"PS2000A_DIGITAL_CHANNEL_{self.timing_chnl}"]  # type: ignore
        self.__trigger_direction_rising = ps.PS2000A_DIGITAL_DIRECTION[  # type: ignore
            "PS2000A_DIGITAL_DIRECTION_RISING"
        ]

        self.__ps_channel_A = ps.PS2000A_CHANNEL["PS2000A_CHANNEL_A"]  # type: ignore
        self.__ps_channel_B = ps.PS2000A_CHANNEL["PS2000A_CHANNEL_B"]  # type: ignore
        self.__ps_port_0 = ps.PS2000A_DIGITAL_PORT["PS2000A_DIGITAL_PORT0"]  # type: ignore
        self.__ps_port_1 = ps.PS2000A_DIGITAL_PORT["PS2000A_DIGITAL_PORT1"]  # type: ignore
        self.__ps_ratio_mode = ps.PS2000A_RATIO_MODE["PS2000A_RATIO_MODE_NONE"]  # type: ignore
        self.__ps_time_unit = ps.PS2000A_TIME_UNITS["PS2000A_NS"]  # type: ignore
        self.__ps_coupling = ps.PS2000A_COUPLING["PS2000A_DC"]  # type: ignore
        self.__ps_range = ps.PS2000A_RANGE["PS2000A_5V"]  # type: ignore
        self.__ps_enabled = 1
        self.__ps_disabled = 0

        if self.timing_chnl >= 8:
            self.__ps_measure_port = self.__ps_port_1
        else:
            self.__ps_measure_port = self.__ps_port_0

    @staticmethod
    def lock():
        global pico_lock
        pico_lock.acquire()

    @staticmethod
    def unlock():
        global pico_lock
        pico_lock.release()

    def start(self):
        """
        Start the measuring task.
        """
        assert self.__handle == None
        assert self.__started == False

        global pico_lock
        assert pico_lock.locked()

        self.__port_buffer = None

        self.__connect()
        keep_con_open = False
        try:
            logging.debug(
                f"PicoMeasure::__configure_channels ({self.picoscope.serial_number})"
            )
            self.__configure_channels()
            logging.debug(
                f"PicoMeasure::__setup_buffers ({self.picoscope.serial_number})"
            )
            self.__setup_buffers()
            logging.debug(
                f"PicoMeasure::__setup_trigger ({self.picoscope.serial_number})"
            )
            self.__setup_trigger()
            logging.debug(
                f"PicoMeasure::__start_streaming ({self.picoscope.serial_number})"
            )
            self.__start_streaming()
            keep_con_open = True
            self.__started = True
        finally:
            if not keep_con_open:
                logging.debug(
                    f"PicoMeasure::__disconnect (start, {self.picoscope.serial_number})"
                )
                self.__disconnect()

    def measure(self) -> float:
        """
        Read and decode the captured timing signal.

        :returns: Returns the timing signal in microseconds.
        """
        assert self.__handle != None
        assert self.__started == True

        global pico_lock
        assert pico_lock.locked()

        try:
            logging.debug(
                f"PicoMeasure::__read_stream ({self.picoscope.serial_number})"
            )
            self.__read_stream()
            logging.debug(
                f"PicoMeasure::__stop_streaming ({self.picoscope.serial_number})"
            )
            self.__stop_streaming()
            time = (
                self.__timing_measure_count
                * self.__actual_sample_int_ns
                / (TEST_TIMING_CLK_DEVIDER * 1000)
            )
            return time
        finally:
            logging.debug(f"PicoMeasure::__disconnect ({self.picoscope.serial_number})")
            self.__disconnect()
            logging.debug(
                f"PicoMeasure::__disconnect (finished, {self.picoscope.serial_number})"
            )
            self.__started = False

    def __connect(self):
        assert self.__handle == None
        try:
            self.__handle = ctypes.c_int16()
            serial_number = ctypes.create_string_buffer(
                str(self.picoscope.serial_number).encode()
            )
            pico_success(ps.ps2000aOpenUnit(ctypes.byref(self.__handle), serial_number))  # type: ignore
        except PicoError as ex:
            self.__handle = None
            raise ex

    def __disconnect(self):
        assert self.__handle != None
        try:
            pico_success(ps.ps2000aCloseUnit(self.__handle))  # type: ignore
        except PicoError as ex:
            logging.warning(
                f"Desconnecting from PicoScope failed with error {ex.type}. {ex.msg}"
            )
        finally:
            self.__handle = None

    def __configure_channels(self):
        assert self.__handle != None

        pico_success(
            ps.ps2000aSetDigitalPort(  # type: ignore
                self.__handle,
                self.__ps_port_0,
                self.__ps_disabled,
                self.__logic_level,
            )
        )
        pico_success(
            ps.ps2000aSetDigitalPort(  # type: ignore
                self.__handle,
                self.__ps_port_1,
                self.__ps_disabled,
                self.__logic_level,
            )
        )
        pico_success(
            ps.ps2000aSetChannel(  # type: ignore
                self.__handle,
                self.__ps_channel_A,
                self.__ps_disabled,
                self.__ps_coupling,
                self.__ps_range,
                0,
            )
        )
        pico_success(
            ps.ps2000aSetChannel(  # type: ignore
                self.__handle,
                self.__ps_channel_B,
                self.__ps_disabled,
                self.__ps_coupling,
                self.__ps_range,
                0,
            )
        )

        # Enable measure port
        pico_success(
            ps.ps2000aSetDigitalPort(  # type: ignore
                self.__handle,
                self.__ps_measure_port,
                self.__ps_enabled,
                self.__logic_level,
            )
        )

    def __setup_buffers(self):
        assert self.__handle != None
        assert self.__port_buffer == None

        self.__port_buffer = np.zeros(shape=self.__buffer_len, dtype=np.int16)

        pico_success(
            ps.ps2000aSetDataBuffer(  # type: ignore
                self.__handle,
                self.__ps_measure_port,
                self.__port_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                self.__buffer_len,
                0,
                self.__ps_ratio_mode,
            )
        )

    def __setup_trigger(self):
        assert self.__handle != None

        dont_care = ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_DONT_CARE"]  # type: ignore
        trigger_true = ps.PS2000A_TRIGGER_STATE["PS2000A_CONDITION_TRUE"]  # type: ignore
        nr_conditions = 1

        trigger_conditions = PS2000A_TRIGGER_CONDITIONS(
            dont_care,
            dont_care,
            dont_care,
            dont_care,
            dont_care,
            dont_care,
            dont_care,
            trigger_true,
        )

        pico_success(
            ps.ps2000aSetTriggerChannelConditions(  # type: ignore
                self.__handle, ctypes.byref(trigger_conditions), nr_conditions
            )
        )

        digital_directions = PS2000A_DIGITAL_CHANNEL_DIRECTIONS(
            self.__ps_measure_channel, self.__trigger_direction_rising
        )
        nr_directions = 1

        pico_success(
            ps.ps2000aSetTriggerDigitalPortProperties(  # type: ignore
                self.__handle, ctypes.byref(digital_directions), nr_directions
            )
        )

    def __stop_streaming(self):
        assert self.__handle != None
        pico_success(ps.ps2000aStop(self.__handle))  # type: ignore

    def __start_streaming(self):
        assert self.__handle != None
        assert self.__reading == False

        self.__actual_sample_int_ns = 0
        smpl_rate = ctypes.c_int32(self.__sample_time_ns)
        max_pre_trigger_smpls = 0
        auto_stop_on = 1
        downsample_ratio = 1
        pico_success(
            ps.ps2000aRunStreaming(  # type: ignore
                self.__handle,
                ctypes.byref(smpl_rate),
                self.__ps_time_unit,
                max_pre_trigger_smpls,
                self.__buffer_len,
                auto_stop_on,
                downsample_ratio,
                self.__ps_ratio_mode,
                self.__buffer_len,
            )
        )
        self.__actual_sample_int_ns = smpl_rate.value
        logging.debug(
            "Requested sample rate for timing test is"
            f" {self.__sample_time_ns}ns. Actually used sample rate is"
            f" {self.__actual_sample_int_ns}ns."
        )

    @staticmethod
    def __streaming_callback(
        handle,
        no_of_samples,
        start_idx,
        overflow,
        trigger_at,
        triggered,
        auto_stop,
        pico_measure_ptr,
    ):
        pico_measure: PicoMeasure = ctypes.cast(
            pico_measure_ptr, ctypes.POINTER(ctypes.py_object)
        ).contents.value

        assert pico_measure.__port_buffer is not None

        if triggered != 0:
            pico_measure.__trigger_index = trigger_at

        if (
            pico_measure.__trigger_index >= 0
            and triggered == 0
            and pico_measure.__port_buffer[start_idx] & pico_measure.timing_chnl_mask
            == 0
        ):
            pico_measure.__reading = False

        pico_measure.__sample_cnt += no_of_samples
        if pico_measure.__sample_cnt >= pico_measure.__buffer_len:
            pico_measure.__reading = False

    def __read_stream(self):
        assert self.__handle is not None
        assert self.__port_buffer is not None
        assert self.__reading is False

        self.__reading = True
        self.__trigger_index = -1
        self.__timing_measure_count = 0
        self.__sample_cnt = 0

        start = time.time()
        c_func_ptr = ps.StreamingReadyType(self.__streaming_callback)  # type: ignore
        pico_measure_ptr = ctypes.cast(
            ctypes.pointer(ctypes.py_object(self)), ctypes.c_void_p
        )

        while self.__reading:
            pico_success(
                ps.ps2000aGetStreamingLatestValues(  # type: ignore
                    self.__handle, c_func_ptr, pico_measure_ptr
                )
            )
            time.sleep(0.001)

        if self.__trigger_index < 0:
            raise TimeoutError()

        self.__timing_measure_count = _measure_timing(
            self.__port_buffer,
            self.__trigger_index,
            chnl_mask=self.timing_chnl_mask,
        )

        logging.debug(
            f"Measuring timing took {int(np.round((time.time() - start) * 1000))}ms."
        )
