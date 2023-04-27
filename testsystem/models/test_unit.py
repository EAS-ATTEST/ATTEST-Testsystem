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

import re
import logging

from .msp430 import MSP430
from .pico_scope import PicoScope
from .connection_info import ConnectionInfo
from testsystem.config import get_config
from testsystem.exceptions import ConfigError
from testsystem.constants import TUTAG_SCOPE


active_test_units: list[TestUnit] = []
all_discovered_connections: list[ConnectionInfo] = []


class TestUnit:
    """
    A Test Unit consists of an MSP430 board and a PicoScope with some predefined
    connections.

    :param msp: The MSP430 used for this Test Unit.
    :param pico: The PicoScope used for this Test Unit.
    :param connections: A list of all available connections between the MSP430 and the
        PicoScope. This list must contain at least the required connections to construct
        a valid Test Unit.
    """

    __test__ = False

    def __init__(
        self,
        msp: MSP430,
        pico: PicoScope | None = None,
        connections: list[ConnectionInfo] = [],
    ):
        self.msp430 = msp
        self.picoscope = pico
        self.__tags: list[str] = []

        for c in connections:
            assert c.msp430 == msp
            assert c.picoscope == pico

        _, cons = self.validate_setup(msp, pico, connections)

        self.connections = cons

        global active_test_units
        active_test_units.append(self)

        if pico is not None:
            self.add_tag(TUTAG_SCOPE)

    def is_available(self) -> bool:
        """
        Check if this test unit is currently availabe.

        :returns: ``True`` if it is available, ``False`` otherwise.
        """
        return self.msp430.is_connected()

    @staticmethod
    def get() -> list[TestUnit]:
        """
        Get all active test units.
        This is a list of test units that were discovered during start-up.
        """
        global active_test_units
        return active_test_units

    @staticmethod
    def set_connections(connections: list[ConnectionInfo]):
        """
        Set globally available connections.

        :param connections: All discoverd connections.
        """
        global all_discovered_connections
        all_discovered_connections = connections

    @staticmethod
    def get_connections() -> list[ConnectionInfo]:
        """
        Get all available connections.

        :returns: All connections discovered during start-up.
        """
        global all_discovered_connections
        return all_discovered_connections

    @staticmethod
    def validate_setup(
        msp: MSP430, picoscope: PicoScope | None, connections: list[ConnectionInfo]
    ) -> tuple[bool, list[ConnectionInfo]]:
        """
        Checks if a specific MSP430 board and a PicoScope can be combined into a Test
        Unit.

        :param msp: MSP430 board
        :param picoscope: PicoScope
        :param connections: All available connections between any devices. They are
            not restricted to the specific MSP430 or PicoScope provided as the previous
            parameters.

        :returns: The first parameter indicates if the MSP430 and the PicoScope can be
            combined into a Test Unit. The second parameter is a subset of connections
            between the two devices used to build a valid Test Unit.
        """

        if picoscope is None:
            return False, []

        required_connections = TestUnit.get_required_connections()

        cons = []
        for r_con in required_connections:
            found = False
            for con in connections:
                if con.msp430 != msp or con.picoscope != picoscope:
                    continue
                if (
                    r_con.msp_port == con.msp_port
                    and r_con.msp_pin == con.msp_pin
                    and r_con.pico_channel == con.pico_channel
                ):
                    cons.append(con)
                    found = True
                    break
            if not found:
                return False, []
        return True, cons

    @classmethod
    def get_timing_channel(cls) -> int:
        """
        Get the digital channel number for timing tests. This is the channel of the
        first :py:attr:`testsystem.config.Config.tu_connections` configuration.

        :returns: The digital channel number.
        """
        required_connections = TestUnit.get_required_connections()
        if len(required_connections) == 0:
            logging.error(
                "Found no connection configuration. Using digital channel 0 for timing"
                " test measures."
            )
            return 0
        return int(required_connections[0].pico_channel.strip("D"))

    @classmethod
    def get_required_connections(cls) -> list[ConnectionInfo]:
        """
        Parses the configuration and returns a list of required connections with a port,
        a pin, and a channel, to form a valid Test Unit.

        :exceptions ConfigError: Is raised if the configuration is invalid.

        :returns: A list of required connections.
        """

        conf = get_config()
        connections = []
        regex_pp = r"^P(?P<port>[0-9]+).(?P<pin>[0-9]+)$"
        regex_c = r"^(?P<chnl>D[0-9]+)$"

        for con_conf in conf.tu_connections:

            def raise_error():
                raise ConfigError(
                    "tu_connections",
                    conf.tu_connections,
                    f"Syntax error in '{con_conf}'.",
                )

            tokens = con_conf.split("-")
            if len(tokens) != 2:
                raise_error()

            pp_match = re.search(regex_pp, tokens[0])
            c_match = re.search(regex_c, tokens[1])
            if pp_match == None and c_match == None:
                pp_match = re.search(regex_pp, tokens[1])
                c_match = re.search(regex_c, tokens[0])
            if pp_match == None or c_match == None:
                raise_error()

            chnl = c_match.group("chnl")

            con = ConnectionInfo(
                int(pp_match.group("port")),
                int(pp_match.group("pin")),
                chnl,
            )
            connections.append(con)

        return connections

    @staticmethod
    def is_config_valid() -> bool:
        """
        Checks whether the required configuration for Test Units is valid.

        :returns: Returns ``True`` if the configuration is valid, ``False`` otherwise.
        """
        try:
            TestUnit.get_required_connections()
            return True
        except ConfigError:
            return False

    @property
    def has_scope(self) -> bool:
        return self.picoscope != None

    def has_tag(self, tag: str | None) -> bool:
        if tag is None:
            return False
        return tag in self.__tags

    def add_tag(self, tag: str):
        if tag not in self.__tags:
            self.__tags.append(tag)

    def remove_tag(self, tag: str):
        if tag in self.__tags:
            self.__tags.remove(tag)
