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

import time
import logging
import ctypes
import numpy as np

from .pico_scope import PicoScope
from .channel_reader import ChannelReader
from testsystem.exceptions import PicoError
from testsystem.constants import PICO_LOGIC_THRESHOLD_VOLTAGE
from picosdk.ps2000a import ps2000a as ps


def pico_success(status):
    if status != 0:
        raise PicoError(status)


class PicoReader:
    """
    This class is used as an interface to the PicoScopes during the discovery process.
    It handles the setup and configuration for the PicoScope,
    reads the streamed data from the scope,
    and decodes the UART signal into a list of bytes for identification.

    :param picoscope: PicoScope instance to be used for capturing.
    """

    def __init__(self, picoscope: PicoScope):
        self.picoscope = picoscope

        self.__logic_level = int(PICO_LOGIC_THRESHOLD_VOLTAGE / 5 * 32767)
        self.__handle = None
        self.__reading = False
        self.__buffer_len = 0
        self.__port_0_buffer = None
        self.__port_1_buffer = None

        self.__ps_port_0 = ps.PS2000A_DIGITAL_PORT["PS2000A_DIGITAL_PORT0"]  # type: ignore
        self.__ps_port_1 = ps.PS2000A_DIGITAL_PORT["PS2000A_DIGITAL_PORT1"]  # type: ignore
        self.__ps_ratio_mode = ps.PS2000A_RATIO_MODE["PS2000A_RATIO_MODE_NONE"]  # type: ignore
        self.__ps_time_unit = ps.PS2000A_TIME_UNITS["PS2000A_US"]  # type: ignore
        self.__ps_enabled = 1
        self.__ps_disabled = 0

        self.__channel_reader = []

    def read(self, baud_rate: int, smpls_per_bit: int, reading_time_ms: float):
        """
        This method first connects to the PicoScope and configures it for capturing.
        The call will fail if there is already an open connection to the scope. The
        reader will close the connection to the PicoScope once capturing, and decoding
        are finished. This call blocks until the described tasks are completed.

        :exceptions PicoError: Is raised when something went wrong when communicating
            with the PicoScope.

        :param baud_rate: The baud rate used by the msp430-identifier program flashed
            to the MSP430 boards.
        :param smpls_per_bit: The number of samples we want to capture for each bit.
            The sample, which is half-time through the bit, will be used for decoding.
        :param reading_time_ms: The capturing time in milliseconds. This value should
            be high enough to include at least one complete id. A reasonable capture
            would contain 2 - 5 ids.
        """
        assert self.__handle == None

        self.__buffer_len = 0
        self.__port_0_buffer = None
        self.__port_1_buffer = None

        smpl_time_us = int(np.round(1000000 / (baud_rate * smpls_per_bit)))
        buffer_length = int(reading_time_ms * 1000 / smpl_time_us)
        self.__connect()
        try:
            self.__channel_reader = []
            self.__configure_channels()
            self.__setup_buffers(smpls_per_bit, buffer_length)
            self.__start_streaming(smpl_time_us)
            self.__read_stream()
            self.__stop_streaming()
        finally:
            self.__disconnect()

    def get_channel_data(self, channel: int) -> list[int]:
        """
        This method returns a list of bytes captured on a given channel. To get some
        results you must first call the
        :py:func:`~testsystem.pico_reader.PicoReader.read` method.

        :param channel: The channel number from where to get the data.
        """
        if len(self.__channel_reader) > channel:
            return self.__channel_reader[channel].get_data()
        else:
            return []

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
                self.__ps_enabled,
                self.__logic_level,
            )
        )
        pico_success(
            ps.ps2000aSetDigitalPort(  # type: ignore
                self.__handle,
                self.__ps_port_1,
                self.__ps_enabled,
                self.__logic_level,
            )
        )

    def __setup_buffers(self, smpls_per_bit: int, buffer_len: int):
        assert self.__handle != None
        assert self.__buffer_len == 0
        assert self.__port_0_buffer == None
        assert self.__port_1_buffer == None
        assert len(self.__channel_reader) == 0

        self.__buffer_len = buffer_len
        self.__port_0_buffer = np.zeros(shape=buffer_len, dtype=np.int16)
        self.__port_1_buffer = np.zeros(shape=buffer_len, dtype=np.int16)

        self.__channel_reader = [ChannelReader(pin, smpls_per_bit) for pin in range(16)]

        pico_success(
            ps.ps2000aSetDataBuffer(  # type: ignore
                self.__handle,
                self.__ps_port_0,
                self.__port_0_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                buffer_len,
                0,
                self.__ps_ratio_mode,
            )
        )
        pico_success(
            ps.ps2000aSetDataBuffer(  # type: ignore
                self.__handle,
                self.__ps_port_1,
                self.__port_1_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                buffer_len,
                0,
                self.__ps_ratio_mode,
            )
        )

    def __stop_streaming(self):
        assert self.__handle != None
        pico_success(ps.ps2000aStop(self.__handle))  # type: ignore

    def __start_streaming(self, smpl_time_us: int) -> int:
        assert self.__handle != None
        assert self.__reading == False

        self.__reading = True
        total_smpls = int(1000000 / smpl_time_us)  # sample for max. 1 second
        smpl_rate = ctypes.c_int32(smpl_time_us)
        max_pre_trigger_smpls = 0
        auto_stop_on = 1
        downsample_ratio = 1
        pico_success(
            ps.ps2000aRunStreaming(  # type: ignore
                self.__handle,
                ctypes.byref(smpl_rate),
                self.__ps_time_unit,
                max_pre_trigger_smpls,
                total_smpls,
                auto_stop_on,
                downsample_ratio,
                self.__ps_ratio_mode,
                self.__buffer_len,
            )
        )
        actual_sample_int_us = smpl_rate.value
        logging.debug(
            f"Requested sample rate for MSP430 pin identification is {smpl_time_us}us."
            f" Actually used sample rate is {actual_sample_int_us}us."
        )
        return actual_sample_int_us

    @staticmethod
    def __streaming_callback(
        handle,
        no_of_samples,
        start_idx,
        overflow,
        trigger_at,
        triggered,
        auto_stop,
        pico_reader_ptr,
    ):
        pico_reader: PicoReader = ctypes.cast(
            pico_reader_ptr, ctypes.POINTER(ctypes.py_object)
        ).contents.value

        end_index = start_idx + no_of_samples
        assert len(pico_reader.__port_0_buffer) >= end_index  # type: ignore
        assert len(pico_reader.__port_1_buffer) >= end_index  # type: ignore
        assert len(pico_reader.__channel_reader) == 16

        # Record data from port 0
        new_data_port_0 = pico_reader.__port_0_buffer[start_idx:end_index]  # type: ignore
        for i in range(0, 8):
            pin_data = new_data_port_0 >> i & 0x1
            pico_reader.__channel_reader[i].record(pin_data)

        # Record data from port 1
        new_data_port_1 = pico_reader.__port_1_buffer[start_idx:end_index]  # type: ignore
        for i in range(0, 8):
            pin_data = new_data_port_1 >> i & 0x1
            pico_reader.__channel_reader[i + 8].record(pin_data)

        if auto_stop:
            pico_reader.__reading = False

    def __read_stream(self):
        assert self.__handle != None

        start = time.time()
        c_func_ptr = ps.StreamingReadyType(self.__streaming_callback)  # type: ignore
        pico_reader_ptr = ctypes.cast(
            ctypes.pointer(ctypes.py_object(self)), ctypes.c_void_p
        )
        while self.__reading:
            pico_success(
                ps.ps2000aGetStreamingLatestValues(  # type: ignore
                    self.__handle, c_func_ptr, pico_reader_ptr
                )
            )
            time.sleep(0.001)
        logging.debug(
            "Capturing identification signals from MSPs took"
            f" {int(np.round((time.time() - start) * 1000))}ms."
        )
