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

import git
import os
import tarfile
import shutil

import test_framework as tf
import testsystem.constants as cnst


data_src_path = os.path.join(cnst.TESTSYSTEM_ROOT, "tests/integration_tests/data")


def delete_test_repo(test_system: tf.TestSystemModel, name: str):
    remote_repo = os.path.join(test_system.git_remote, name)
    src_repo = os.path.join(data_src_path, name)
    local_repo = os.path.join(test_system.git_local, name)
    if os.path.exists(local_repo):
        shutil.rmtree(local_repo)
    if os.path.exists(remote_repo):
        shutil.rmtree(remote_repo)
    if os.path.exists(src_repo):
        shutil.rmtree(src_repo)


def get_src_repo(test_system: test_system.TestSystem, name: str) -> git.Repo:  # type: ignore
    src_tar = os.path.join(data_src_path, f"{name}.tar.gz")
    assert os.path.exists(
        src_tar
    ), f"No source archive found for group {name}. Path={src_tar}"
    delete_test_repo(test_system, name)
    with tarfile.open(src_tar) as f:
        f.extractall(data_src_path)

    src_repo = os.path.join(data_src_path, name)
    return git.Repo(src_repo)  # type: ignore


def setup_empty_group_repo(test_system: test_system.TestSystem, name: str) -> git.Repo:  # type: ignore
    delete_test_repo(test_system, "RTOS_SS00_GroupInit")
    delete_test_repo(test_system, name)
    repo = get_src_repo(test_system, "RTOS_SS00_GroupInit")
    remote_repo = os.path.join(test_system.git_remote, name)
    local_repo = os.path.join(test_system.git_local, name)
    repo.git.config("--global", "--add", "safe.directory", repo.working_dir)
    repo.git.init("--bare", remote_repo)
    repo.git.remote("add", "test", remote_repo)
    repo.git.push("--set-upstream", "test", "master")
    repo.git.remote("remove", "test")
    return git.Repo.clone_from(remote_repo, local_repo)  # type: ignore


def setup_test_repo(test_system: test_system.TestSystem, name: str) -> git.Repo:  # type: ignore
    """
    Setup a remote test repository from an existing archived git repo and clone it
    into a new directory.

    :param name: The name of the .tar.gz file without the ending.

    :returns: A new clone of the remote test repository.
    """
    delete_test_repo(test_system, name)
    repo = get_src_repo(test_system, name)
    remote_repo = os.path.join(test_system.git_remote, name)
    local_repo = os.path.join(test_system.git_local, name)
    repo.git.config("--global", "--add", "safe.directory", repo.working_dir)
    repo.git.init("--bare", remote_repo)
    repo.git.remote("add", "test", remote_repo)
    repo.git.push("--set-upstream", "test", "master")
    repo.git.push("test", "--tags")
    repo.git.remote("remove", "test")
    return git.Repo.clone_from(remote_repo, local_repo)  # type: ignore
