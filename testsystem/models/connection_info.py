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

from .msp430 import MSP430
from .pico_scope import PicoScope


class ConnectionInfo:
    """
    This class stores information about a connection between an MSP430 board an a
    PicoScope.

    :param port: The port on the MSP430.
        Port and pin are required to identify the connection on the MSP side uniquely.
    :param pin: The pin on the MSP430.
        Port and pin are required to identify the connection on the MSP side uniquely.
    :param channdel: The channel on the PicoScope.
        The channel string starts with 'A' for analog or 'D' for a digital channel,
        followed by its number.
    :param device_id: The id which the PicoScope decoded from the signal it received.
    :param msp: The msp object on one side of the connection.
    :param pico: The PicoScope object on one side of the connection.
    """

    def __init__(
        self,
        port: int,
        pin: int,
        channel: str,
        device_id: int | None = None,
        msp: MSP430 | None = None,
        pico: PicoScope | None = None,
    ):
        self.device_id = device_id
        self.msp_port = port
        self.msp_pin = pin
        self.pico_channel = channel
        self.msp430 = msp
        self.picoscope = pico
