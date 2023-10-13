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
from inspect import Parameter

import re
import os
import json
import time
import logging

import testsystem.utils as utils

from testsystem.constants import CONFIG_CACHE_TIME_S

last_config_timestamp = 0.0
last_config: Config | None = None
logging_enabled: bool = False


class Config:
    """
    Configuration class for the RTOS Test System. Members can be overwritten via
    environment variables or a JSON config file. Details on how configuration works can
    be found in section :ref:`Configuration`. To set a list parameter with an
    environment variable, concatenate the values with ``;``.

    The following labels describe how a property can be set or modified:

    * :guilabel:`env`: Configuration via environment variable is possible.
    * :guilabel:`file`: Configuration via JSON config file is possible. This usually also implies :guilabel:`env`.
    * :guilabel:`dyn`: Dynamically changing the configuration will affect the running system.

    """

    #: | :guilabel:`env` :guilabel:`file`
    #: | If set to ``True``, the test system runs its hello world equivalent,
    #:   displaying some general information.
    run_hello_testsystem: bool = False

    #: | Flag to enable configuration through environment variables.
    conf_enable_env: bool = True

    #: | :guilabel:`env` :guilabel:`dyn`
    #: | Flag to enable configuration through the config file.
    conf_enable_file: bool = True

    #: | :guilabel:`env` :guilabel:`dyn`
    #: | Path to the JSON config file.
    conf_file: str = "/host/config.json"

    #: | :guilabel:`env` :guilabel:`file`
    #: | Set the database type used for persisting data. Available options are:
    #:   ``sqlite``, ``mysql`` \ .
    db_type: str = "sqlite"

    #: | :guilabel:`env` :guilabel:`dyn`
    #: | Path to the Database file.
    db_file: str = "/host/testsystem.db"

    #: | :guilabel:`env` :guilabel:`dyn`
    #: | Database user name.
    db_user: str = "testsystem"

    #: | :guilabel:`env` :guilabel:`dyn`
    #: | Database password.
    db_password: str = "Password1"

    #: | :guilabel:`env` :guilabel:`dyn`
    #: | Database name.
    db_database: str = "testsystem"

    #: | :guilabel:`env` :guilabel:`dyn`
    #: | Database server/host.
    db_server: str = "127.0.0.1"

    #: | :guilabel:`env` :guilabel:`file`
    #: | Option to define where to wirte testsystem logs.
    log_file: str = "/host/testsystem.log"

    #: | :guilabel:`env` :guilabel:`file`
    #: | Specify the log level to use for testsystem logs. Available options are:
    #: | ``DEBUG``, ``INFO``, ``WARN``, ``ERROR``, ``CRITICAL``\ .
    log_level: str = "DEBUG"

    #: | :guilabel:`env` :guilabel:`file`
    #: | Defines which connections must be available between an MSP430 and a PicoScope
    #:   to form a :py:class:`~testsystem.test_unit.TestUnit`. The syntax for the MSP430
    #:   pin is P<Port>.<Pin>, and for the PicoScope channel, this would be D<Channel>,
    #:   where D stands for digital channels. The pin and channel strings are combined
    #:   with a ``-``.
    #: |
    #: | ``P1.2-D3`` would be a valid configuration for a required connection between
    #:   port 1.2 and digital channel 3.
    tu_connections: list[str] = ["P6.0-D7"]

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | A list of group ids. This is used to determine which groups actively
    #:   participate and should get tested. You can remove or add existing groups
    #:   during runtime.
    group_ids: list[int] = [1]

    #: | :guilabel:`env` :guilabel:`file`
    #: | Term name.
    term: str = "SS23"

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | Enables timing test cases. Timing tests won't be included in test runs if this
    #:   is set to ``False``.
    enable_timing_tests: bool = True

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | The current exercise number. Test runs will also include all test cases from
    #:   previous exercises.
    exercise_nr: int = 0

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | This flag is used to gracefully shut down the testsystem.
    stop: bool = False

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | Git server with all repos. You can use absolute paths to use the filesystem as
    #:   remote.
    git_server: str = "ssh://git@iti-gitlab.tugraz.at"

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | Relative path on git server root where to find student repos.
    git_student_path: str = "eas/teaching/RTOS_SS23"

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | Relative path on git server root where to find public repos.
    git_public_path: str = "eas/teaching/RTOS_SS23"

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | Relative path to the system repository. This repository is used to push test reports, to
    #:   configure the testsystem and for monitoring.
    git_system_path: str = "eas/teaching/RTOS_SS23/Testsystem_Reports_SS23"

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | Name for primary git branch. Usually this is ``master`` or ``main``.
    git_primary_branch_name: str = "main"

    #: | :guilabel:`env` :guilabel:`file`
    #: | Path to the test case directory.
    tc_root_path = "/testcases"

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | Parameter to specify when to reset group priorities. The value is given in
    #:   hours after which the priorities are reset to default.
    prio_reset_h = 24

    #: | :guilabel:`env` :guilabel:`file` :guilabel:`dyn`
    #: | This parameter provides a list of tags that must be tested anyways. This
    #:   guarantees a test report for special commits that might be skipped by regular
    #:   scheduling. Tag values are case-insensitive.
    force_test_tags: list[str] = ["ex1", "ex2", "ex3", "ex4", "ex5", "ex6"]

    def get_group_commit_link(self, group_name: str, commit_hash: str) -> str:
        sub_path = f"{self.git_student_path}/{group_name}/-/tree/{commit_hash}"
        url = utils.url_builder(self.git_server, sub_path)
        return utils.url_as_web_link(url)


def enable_logging():
    global logging_enabled
    logging_enabled = True


def get_config_from_env() -> dict:
    env_prefix = "ATTEST_"
    pattern = re.compile(r"{prefix}\w+".format(prefix=env_prefix))
    conf = {}
    for k, v in os.environ.items():
        if pattern.match(k):
            if ";" in v:
                v = v.split(";")
            conf[k.replace(env_prefix, "")] = v
    return conf


def get_config_from_file(path) -> dict:
    with open(path, "r") as f:
        return json.loads(f.read())


def camel_case_to_snake_case(str):
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def clear_cache():
    global last_config, last_config_timestamp
    last_config = None
    last_config_timestamp = 0.0


def get_config() -> Config:
    """
    Function to request current configuration.
    """
    global last_config
    global last_config_timestamp
    if (
        last_config is not None
        and time.time() - last_config_timestamp <= CONFIG_CACHE_TIME_S
    ):
        return last_config

    global logging_enabled

    config = Config()

    if config.conf_enable_env:
        env_config = get_config_from_env()
        for param in env_config:
            config.__dict__[param.lower()] = env_config[param]

    if config.conf_enable_file:
        try:
            file_config = get_config_from_file(config.conf_file)
            for param in file_config:
                config.__dict__[camel_case_to_snake_case(param)] = file_config[param]
        except OSError:
            pass

    last_config_timestamp = time.time()
    last_config = config
    return config
