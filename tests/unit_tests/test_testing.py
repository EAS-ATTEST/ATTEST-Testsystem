import pytest
import unittest.mock as mock

from testsystem.testing import *


class SerialMock:
    def __init__(self, msg="") -> None:
        if isinstance(msg, str):
            msg = msg.encode()
        self._msg = msg
        self._msg_i = 0

    @property
    def msg(self) -> str:
        return self._msg.decode()

    @property
    def bypte_msg(self) -> bytes:
        return self._msg

    def read(self, len):
        s = self._msg_i
        self._msg_i += len
        return self._msg[s : self._msg_i]


def test_read_port_output_definition():
    port = SerialMock()
    keys = ["output", "timeout_output", "runtime", "is_timeout"]
    result = read_port(port, 0, overflow_check_time=0)
    assert all(k in result.keys() for k in keys)


@pytest.mark.parametrize(
    "msg, exp_output, read_time",
    [
        pytest.param(
            b"Hello World! This is a test message.",
            b"Hello World! This is a test message.",
            0.1,
            id="Normal reading",
        ),
        pytest.param(
            b"Hello World! This is a test message.",
            b"",
            0,
            id="No read time",
        ),
    ],
)
def test_read_port(msg, exp_output, read_time):
    port = SerialMock(msg)
    result = read_port(port, read_time, overflow_check_time=0)
    assert result["output"] == exp_output


def test_read_port_timeout():
    port = SerialMock("Hello World!")
    result = read_port(port, 0, overflow_check_time=0.1)
    assert result["output"] == b""
    assert result["timeout_output"] == port.bypte_msg
    assert result["is_timeout"] == True


def test_read_port_runtime_measure():
    # msg2 is available after msg1 and a min waiting time
    msg1 = "AAAA".encode()
    msg2 = "BBBB".encode()
    msg_i = 0
    msg_f = False
    wait_time = 0.1
    start_time = 0

    def _read(l):
        nonlocal msg_i, msg_f, start_time
        s = msg_i
        msg_i += l
        if not msg_f:
            r = msg1[s:msg_i]
            if msg_i >= len(msg1):
                msg_f = True
                msg_i = 0
                start_time = time.time()
            return r
        else:
            x = time.time() - start_time
            if x < wait_time:
                msg_i = 0
                return bytes(0)
            return msg2[s:msg_i]

    port = mock.MagicMock()
    port.read = _read
    result = read_port(port, 0.2, overflow_check_time=0.0)
    assert result["output"] == msg1 + msg2
    assert result["timeout_output"] == None
    assert result["runtime"] >= (wait_time - 0.001)  # Timing uncertainty
    assert result["is_timeout"] == False
