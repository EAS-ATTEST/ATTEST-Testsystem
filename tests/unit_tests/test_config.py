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

import testsystem.config as cnf
import unittest.mock as mock
import json
import os


@mock.patch("testsystem.config.CONFIG_CACHE_TIME_S", 0)
@mock.patch("testsystem.config.get_config_from_env")
def test_override_default_config_with_env_config(mock):
    expected = "mysql"
    mock.return_value = {"DB_TYPE": expected}
    assert cnf.get_config().db_type == expected


@mock.patch("testsystem.config.CONFIG_CACHE_TIME_S", 0)
@mock.patch("testsystem.config.get_config_from_file")
def test_override_default_config_with_file_config(mock):
    expectedType = "mysql"
    expectedFlag = False
    mock.return_value = {"dbType": expectedType, "ConfEnableEnv": expectedFlag}
    c = cnf.get_config()
    assert c.db_type == expectedType
    assert c.conf_enable_env == expectedFlag


@mock.patch("testsystem.config.CONFIG_CACHE_TIME_S", 0)
@mock.patch("testsystem.config.get_config_from_env")
@mock.patch("testsystem.config.get_config_from_file")
def test_override_env_config_with_file_config(mock_file, mock_env):
    expected = "mysql"
    mock_env.return_value = {"DB_TYPE": "not expected"}
    mock_file.return_value = {"dbType": expected}
    assert cnf.get_config().db_type == expected


@mock.patch("testsystem.config.CONFIG_CACHE_TIME_S", 0)
@mock.patch("testsystem.config.get_config_from_env")
@mock.patch("testsystem.config.get_config_from_file")
def test_disable_file_config_from_env(mock_file, mock_env):
    mock_env.return_value = {"CONF_ENABLE_FILE": False}
    cnf.get_config()
    mock_file.assert_not_called()


@mock.patch("testsystem.config.CONFIG_CACHE_TIME_S", 0)
@mock.patch("testsystem.config.get_config_from_env")
def test_read_config_file(mock_env):
    expected = "mssql"
    path = "./TESTARTEFACT-config.json"
    mock_env.return_value = {"CONF_FILE": path}

    if os.path.exists(path):
        os.remove(path)

    with open(path, "w") as f:
        data = {"dbType": expected}
        json.dump(data, f)

    conf = cnf.get_config()

    os.remove(path)
    assert conf.db_type == expected


@mock.patch("testsystem.config.CONFIG_CACHE_TIME_S", 0)
@mock.patch("testsystem.config.open")
def test_read_config_file_throws_error(mock_open):
    mock_open.side_effect = OSError()

    conf = cnf.get_config()

    assert conf.db_type == cnf.Config.db_type
