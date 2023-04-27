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

import testsystem.constants as const


class ConfigError(Exception):
    def __init__(self, parameter, value, msg: str | None = None):
        self.parameter = parameter
        self.value = value
        self.msg = msg

    def __repr__(self) -> str:
        msg = (
            f"The value '{self.value}' is invalid for configuration parameter"
            f" '{self.parameter}'. Check the documentation for further information. "
        )
        if self.msg != None and len(self.msg) > 0:
            msg += self.msg
        return msg


class ParsingError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self) -> str:
        return f"ParsingError: {self.msg}"


class PicoError(Exception):
    def __init__(self, code):
        self.code = code
        self.type = const.PICO_ERROR_CODES[code][0]
        self.msg = const.PICO_ERROR_CODES[code][1]

    def __str__(self):
        return f"PicoScope error {self.type}. {self.msg}"

    def __repr__(self) -> str:
        return f"PicoScope error {self.type}. {self.msg}"


class IdentificationError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class DetectError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class NotConnectedError(DetectError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class NoSignalError(DetectError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidTXPauseError(DetectError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidSignalError(DetectError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class StartBitError(DetectError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class StopBitError(DetectError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class DecodeError(Exception):
    msg: str = ""

    def __init__(self, msg: str, *args: object) -> None:
        self.msg = msg
        super().__init__(*args)


class MSPError(Exception):
    def __init__(self, msg: str, *args: object) -> None:
        # self.msp430 = msp
        self.msg = msg
        super().__init__(*args)


class MSPConnectionError(MSPError):
    def __init__(self, msg: str, *args: object) -> None:
        super().__init__(msg, *args)


class GitError(Exception):
    def __init__(self, msg: str, *args: object) -> None:
        self.msg = msg
        super().__init__(*args)


class TestCaseError(Exception):
    __test__ = False

    def __init__(self, msg: str, *args: object) -> None:
        self.msg = msg
        super().__init__(*args)


class BuildError(Exception):
    def __init__(
        self,
        msg: str,
        output: str | None = None,
        error: str | None = None,
        *args: object,
    ) -> None:
        self.msg = msg
        self.output = output
        self.error = error
        super().__init__(*args)


class FlashError(Exception):
    def __init__(
        self,
        msg: str,
        output: str | None = None,
        error: str | None = None,
        *args: object,
    ) -> None:
        self.msg = msg
        self.output = output
        self.error = error
        super().__init__(*args)


class FirmewareError(Exception):
    def __init__(self, msg: str, *args: object) -> None:
        self.msg = msg
        super().__init__(*args)


class ProcessError(Exception):
    def __init__(self, msg: str, *args: object) -> None:
        self.msg = msg
        super().__init__(*args)

    def __repr__(self) -> str:
        return self.msg
