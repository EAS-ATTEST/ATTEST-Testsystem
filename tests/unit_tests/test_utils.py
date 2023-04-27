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

import testsystem.utils as utils
import unittest.mock as mock
import pytest


@pytest.mark.parametrize("value", ["TRUE", "True", "true", "1", (1), (True)])
def test_bool_convertion_to_true(value):
    assert True == utils.to_bool(value)


@pytest.mark.parametrize("value", ["FALSE", "False", "false", "0", (0), (False)])
def test_bool_convertion_to_false(value):
    assert False == utils.to_bool(value)


def test_unsupported_bool_convertion():
    with pytest.raises(NotImplementedError) as e_info:
        utils.to_bool(None)


@mock.patch("testsystem.utils.Popen")
def test_external_task_returnes_control_character(m_popen):
    process = mock.MagicMock()
    proc_return = b"Hello\x96World", b""
    process.communicate = mock.MagicMock(return_value=proc_return)
    process.returncode = 3

    m_popen.return_value = process

    code, output, err = utils.run_external_task("cmd")

    assert 3 == code
    assert "HelloWorld" == output
    assert "" == err


@pytest.mark.parametrize(
    "data",
    [
        {"timestamp": 1656669600000, "expected": "01.07.2022 12:00:00"},
        {"timestamp": 1667300400000, "expected": "01.11.2022 12:00:00"},
        {"timestamp": 1669383878000, "expected": "25.11.2022 14:44:38"},
    ],
)
def test_convert_timestamp_to_str(data):
    result = utils.to_local_time_str(data["timestamp"])
    assert data["expected"] == result


@pytest.mark.parametrize(
    "data",
    [
        {
            "root": "ssh://git@server.com",
            "sub": "dir1",
            "args": [],
            "expected": "git@server.com:dir1",
        },
        {
            "root": "ssh://git@server.com",
            "sub": "dir1",
            "args": ["dir2"],
            "expected": "git@server.com:dir1/dir2",
        },
        {
            "root": "ssh://git@server.com",
            "sub": "dir1/dir2",
            "args": [],
            "expected": "git@server.com:dir1/dir2",
        },
        {
            "root": "ssh://git@server.com",
            "sub": "dir1",
            "args": ["dir2", "dir3"],
            "expected": "git@server.com:dir1/dir2/dir3",
        },
        {
            "root": "ssh://git@server.com",
            "sub": "/dir1",
            "args": ["/dir2/"],
            "expected": "git@server.com:dir1/dir2",
        },
        {
            "root": "git@server.com",
            "sub": "dir1",
            "args": [],
            "expected": "git@server.com:dir1",
        },
        {
            "root": "ssh://git@server.com",
            "sub": "",
            "args": [],
            "expected": "git@server.com",
        },
    ],
)
def test_url_builder_ssh(data):
    result = utils.url_builder(data["root"], data["sub"], *data["args"])
    assert data["expected"] == result


@pytest.mark.parametrize(
    "data",
    [
        {
            "root": "https://server.com",
            "sub": "dir1",
            "args": [],
            "expected": "https://server.com/dir1",
        },
        {
            "root": "https://server.com",
            "sub": "dir1",
            "args": ["dir2"],
            "expected": "https://server.com/dir1/dir2",
        },
        {
            "root": "https://server.com",
            "sub": "dir1/dir2",
            "args": [],
            "expected": "https://server.com/dir1/dir2",
        },
        {
            "root": "https://server.com",
            "sub": "dir1",
            "args": ["dir2", "dir3"],
            "expected": "https://server.com/dir1/dir2/dir3",
        },
        {
            "root": "https://server.com",
            "sub": "/dir1",
            "args": ["/dir2/"],
            "expected": "https://server.com/dir1/dir2",
        },
        {
            "root": "server.com",
            "sub": "dir1",
            "args": [],
            "expected": "https://server.com/dir1",
        },
        {
            "root": "server.com",
            "sub": "",
            "args": [],
            "expected": "https://server.com",
        },
    ],
)
def test_url_builder_https(data):
    result = utils.url_builder(data["root"], data["sub"], *data["args"])
    assert data["expected"] == result


@pytest.mark.parametrize(
    "data",
    [
        {
            "root": "/workspace",
            "sub": "dir1",
            "args": [],
            "expected": "/workspace/dir1",
        },
        {
            "root": "/workspace",
            "sub": "dir1",
            "args": ["dir2"],
            "expected": "/workspace/dir1/dir2",
        },
        {
            "root": "/workspace",
            "sub": "dir1/dir2",
            "args": [],
            "expected": "/workspace/dir1/dir2",
        },
        {
            "root": "/workspace",
            "sub": "dir1",
            "args": ["dir2", "dir3"],
            "expected": "/workspace/dir1/dir2/dir3",
        },
        {
            "root": "/workspace",
            "sub": "/dir1",
            "args": ["/dir2"],
            "expected": "/workspace/dir1/dir2",
        },
        {
            "root": "/workspace",
            "sub": "dir1",
            "args": [],
            "expected": "/workspace/dir1",
        },
        {
            "root": "/workspace/dir1/",
            "sub": "dir2/",
            "args": ["/dir3/"],
            "expected": "/workspace/dir1/dir2/dir3",
        },
        {
            "root": "/workspace",
            "sub": "",
            "args": [],
            "expected": "/workspace",
        },
    ],
)
def test_url_builder_directory_path(data):
    result = utils.url_builder(data["root"], data["sub"], *data["args"])
    assert data["expected"] == result


@pytest.mark.parametrize(
    "data",
    [
        {
            "url": "ssh://git@server.com/dir1/dir2",
            "expected": "https://server.com/dir1/dir2",
        },
        {
            "url": "ssh://git@server.com",
            "expected": "https://server.com",
        },
        {
            "url": "git@server.com:dir1/dir2",
            "expected": "https://server.com/dir1/dir2",
        },
        {
            "url": "git@server.com",
            "expected": "https://server.com",
        },
        {
            "url": "/dir1/dir2",
            "expected": "file:///dir1/dir2",
        },
        {
            "url": "https://server.com/dir1",
            "expected": "https://server.com/dir1",
        },
        {
            "url": "server.com/dir1",
            "expected": "https://server.com/dir1",
        },
        {
            "url": "server.com",
            "expected": "https://server.com",
        },
    ],
)
def test_url_as_web_link(data):
    result = utils.url_as_web_link(data["url"])
    assert data["expected"] == result
