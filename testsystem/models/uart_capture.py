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

import numpy as np

from testsystem.exceptions import DetectError, StartBitError, StopBitError


def _read_uart_byte(signal, samples_per_bit):
    signal_start = -1
    for i in range(0, len(signal)):
        if signal[i] == 0:
            signal_start = i
            break

    if signal_start < 0:
        return None, len(signal)

    signal_end = int(np.ceil(signal_start + 10 * samples_per_bit))
    if signal_end > len(signal):
        return None, len(signal)

    if signal[int(signal_start + samples_per_bit / 2)] != 0:  # start bit must be 0
        raise StartBitError()

    data_start = signal_start + samples_per_bit  # add start bit
    bit_array = [
        signal[int(data_start + ((i + 0.5) * samples_per_bit))] for i in range(0, 8)
    ]

    if signal[int(data_start + 8.5 * samples_per_bit)] != 1:  # stop bit must be 1
        raise StopBitError()

    byte_value = 0
    for bit in bit_array:
        byte_value = (byte_value >> 1) + (int(bit) << 7)

    assert byte_value >= 0 and byte_value < 256

    return byte_value, signal_end


class UARTCapture:
    """
    Container class that stores and decodes a single UART byte signal.
    """

    channel: int = -1

    def __init__(self, smpls_per_bit: int):
        self.smpls_per_bit = smpls_per_bit
        self.buffer_length = (
            smpls_per_bit * 12
        )  # start bit | 8 data bits | stop bit | 2 spacer bits
        self.buffer = np.zeros(shape=0)
        self.__find_start = True

    @property
    def complete(self) -> bool:
        """
        Check if capturing a full byte is completed.
        """
        return len(self.buffer) == self.buffer_length

    def capture(self, data) -> int:
        """
        Push new signal data.

        :param data: UART data.

        :returns: The length of the consumed data.
        """
        start_index = 0
        if self.__find_start:
            while start_index < len(data):
                if data[start_index] == 0:
                    self.__find_start = False
                    break
                start_index += 1

        start_size = len(self.buffer)
        self.buffer = np.concatenate((self.buffer, data[start_index:]))
        if len(self.buffer) > self.buffer_length:
            self.buffer = self.buffer[0 : self.buffer_length]
        return start_index + len(self.buffer) - start_size

    def is_valid(self) -> bool:
        """
        Check if this capture is valid.

        :returns: ``True`` if it is valid, ``False`` otherwise.
        """
        try:
            byte, _ = _read_uart_byte(self.buffer, self.smpls_per_bit)
            return byte != None
        except DetectError:
            return False

    def get_byte(self) -> int | None:
        """
        Get the byte value of the UART signal recorded by this capture.

        :returns: Byte or ``None`` for an invalid signal.
        """
        byte, _ = _read_uart_byte(self.buffer, self.smpls_per_bit)
        return byte
