import pytest
import unittest.mock as mock

from testsystem.testing import *


def test_read_port_output_definition():
    keys = ["output", "timeout_output", "runtime", "is_timeout"]
    port_output = read_port(None, 0)
    assert all(k in port_output.keys() for k in keys)
