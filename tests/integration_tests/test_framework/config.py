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

import os
import json
import testsystem.config as cnf

sys_repo_name = "Testsystem_Reports"


def setup_config(conf_file_dir: str):
    if not os.path.exists(conf_file_dir):
        os.mkdir(conf_file_dir)
    conf_file_name = f"config.json"
    conf_file = os.path.join(conf_file_dir, conf_file_name)
    with open(conf_file, "w") as f:
        f.write(
            "{"
            '"term": "SS00",'
            '"group_ids": [],'
            '"exercise_nr": 0,'
            '"git_server": "",'
            '"git_student_path": "",'
            '"git_public_path": "",'
            f'"git_system_path": "{sys_repo_name}"'
            "}"
        )
    os.environ["ATTEST_CONF_FILE"] = conf_file
    return conf_file


def delete_config(conf_file: str):
    cnf.clear_cache()
    os.unsetenv("ATTEST_CONF_FILE")
    os.remove(conf_file)


def set_config(
    conf_file: str,
    property: str,
    value: str | int | bool | list[str] | list[int] | list[bool],
):
    with open(conf_file, "r+") as f:
        json_data = json.load(f)
        json_data[property] = value
        f.seek(0, 0)
        json.dump(json_data, f)
        f.truncate()


def get_config(property: str) -> str:
    config = cnf.get_config()
    return getattr(config, property)
