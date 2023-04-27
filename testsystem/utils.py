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

import uuid
import logging
import pandas as pd

from subprocess import Popen, PIPE, TimeoutExpired


def get_uuid() -> int:
    return uuid.uuid4().int


def url_builder(root: str, sub: str, *args: str) -> str:
    _root = root.rstrip("/")
    _sub = sub.strip("/")
    _args = []
    for arg in args:
        _args.append(arg.strip("/"))

    _arg_sub = ""
    _arg_sub = "/".join(_args)

    url = ""
    if _root.startswith("/"):
        url = "/".join([_root, _sub]).rstrip("/")
    elif "git@" in _root or "ssh://" in _root:
        _root = _root.replace("ssh://", "")
        url = ":".join([_root, _sub]).rstrip(":")
    else:
        _root = "https://" + _root.replace("https://", "")
        url = "/".join([_root, _sub]).rstrip("/")

    if len(args) > 0:
        url = "/".join([url, _arg_sub])
    return url


def url_as_web_link(url: str) -> str:
    url = url_builder(url, "")
    if url.startswith("git@"):
        return "https://" + url.replace("git@", "").replace(":", "/")
    elif url.startswith("/"):
        return "file://" + url
    else:
        return url


def run_external_task(args, input=None, timeout=10) -> tuple[int, str, str]:
    """
    Interface to safely run an external task. This function should be used any time the
    test system requires an additional tool.

    :param args: Arguments to the external task.
    :param input: An optional input after the task is stared.
    :param timeout: A timeout when to kill the external task and return to the test
        system.

    :returns: The first parameter is the return code from the process. The second
        parameter is the standard output of the process and the last parameter is the
        error output of the process.
    """
    process = Popen(args, stdin=PIPE, stderr=PIPE, stdout=PIPE)
    logging.debug(f"Run external task (PID={process.pid}): {args}")
    try:
        if input is None:
            stdout, stderr = process.communicate(timeout=timeout)
        else:
            stdout, stderr = process.communicate(timeout=timeout, input=input.encode())
        ret_code = process.returncode

        err_msg = stderr.decode(errors="ignore").strip("\n")
        out_msg = stdout.decode(errors="ignore").strip("\n")

        logging.debug(f"External task exited with code {ret_code}.")

        return ret_code, out_msg, err_msg
    except TimeoutExpired as ex:
        raise ex
    finally:
        process.kill()


def to_bool(value: int | str) -> bool:
    """
    Convert an integer or string to bool.

    :param value: Bool variable as integer or string type.

    :returns: Actual bool value.
    """
    if isinstance(value, int):
        return value != 0
    elif isinstance(value, str):
        return value.lower() in ("true", "1")
    else:
        raise NotImplementedError(
            f"Bool convertion for type {type(value)} is not implemented."
        )


def to_local_time_str(
    timestamp: float | int, strftime: str = "%d.%m.%Y %H:%M:%S"
) -> str:
    """
    Converts a timestamp to the local time format. This should be used any time a
    conversion from a timestamp to a readable date time is required.

    :param timestamp: Timestamp in unix millis.
    :param strftime: A format string for the date time convertion.

    :returns: The timestamp as date time string.
    """
    ts = pd.Timestamp(timestamp, unit="ms", tz="Europe/Vienna")
    return ts.strftime(strftime)
