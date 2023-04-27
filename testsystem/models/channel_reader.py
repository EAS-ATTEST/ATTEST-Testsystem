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

from .uart_capture import UARTCapture


class ChannelReader:
    """
    Class to capture long UART signals on a PicoScope channel.
    """

    def __init__(self, pin: int, smpls_per_bit: int):
        self.pin = pin
        self.smpls_per_bit = smpls_per_bit
        self.active_capture = None
        self.capture_list: list[UARTCapture] = []

    def record(self, data):
        """
        Record signal data.

        :param data: New data to add.
        """
        index = 0
        while index < len(data):
            if self.active_capture == None:
                self.active_capture = UARTCapture(self.smpls_per_bit)
            index += self.active_capture.capture(data[index:])
            if self.active_capture.complete:
                self.capture_list.append(self.active_capture)
                self.active_capture = None

    def get_data(self) -> list[int]:
        """
        Get a list of bytes that were decoded from the recorded UART signal.

        :returns: List of bytes.
        """
        data = []
        for capture in self.capture_list:
            if capture.is_valid():
                data.append(capture.get_byte())
        return data
