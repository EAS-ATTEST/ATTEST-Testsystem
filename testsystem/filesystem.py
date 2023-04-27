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
import logging

logging.getLogger("git").setLevel(logging.WARNING)
import git
import sys
import glob
import time
import shutil
import random
import threading
import numpy as np
import testsystem.utils as utils

from testsystem.config import get_config
from testsystem.exceptions import GitError, TestCaseError

from testsystem.constants import (
    MSP_ID_IDENTIFIER_PATH,
    TEST_HEADER_FILES,
    TEST_DEFINITION_FILE,
    TEST_OUTPUT_DIR_NAME,
    TEST_TESTBENCHE_DIR_NAME,
    GIT_LOCAL_ROOT_DIR,
    TEST_ENVIRONMENT_DIRECTORY,
    TEST_GROUP_SRC_FILES,
    GIT_PUBLIC_NAME_TEMPLATE,
    GIT_RETRIES,
    GIT_PUBLIC_CACHE_TIME_S,
    GIT_RESULT_BRANCH_NAME,
    MSP_ID_GENERATOR_DEFINE,
    MSP_ID_DEVICE_ID_TEMPLATE,
)

_git_lock = threading.Lock()
_public_repo_timestamp = 0
_public_repo_commit = ""


class TestEnv:
    """
    Secure test environment for a group on a specific commit.

    :param directory: The directory of the git repository.
    :param state: The state in whicht to checkout the repository. This can be a tag or commit hash.
    """

    __test__ = False

    def __init__(self, group_name: str, commit: str) -> None:
        global _git_lock
        assert (
            _git_lock.locked()
        ), "Use setup_test_env() to initialize a new test environment."

        public_src_dir = _get_local_public_git_directory()
        group_src_dir = _get_local_group_git_directory(group_name)

        repo = git.Repo(group_src_dir)  # type: ignore
        repo.git.checkout(commit)
        self.__commit = commit
        self.__commit_time = repo.head.commit.committed_date * 1000
        msg = repo.head.commit.message
        if isinstance(msg, bytes):
            msg = msg.decode()
        self.__commit_msg = msg

        self.__env_id = commit
        self.__group_name = group_name
        self.__env_dir = _get_test_env_dir(self.__env_id)

        if os.path.exists(self.__env_dir):
            shutil.rmtree(self.__env_dir)

        conf = get_config()
        default_group_dir_name = f"RTOS_{conf.term}_GroupXX"

        # Copy public repo
        self.__env_public_dir = _get_test_env_public_dir(self.__env_id)
        self.__env_group_dir = _get_test_env_group_dir(self.__env_id, group_name)
        shutil.copytree(os.path.join(public_src_dir), self.__env_public_dir)
        shutil.copytree(
            os.path.join(public_src_dir, default_group_dir_name), self.__env_group_dir
        )

        # Copy setup
        tc_setup_src_dir = os.path.join(
            conf.tc_root_path, TEST_TESTBENCHE_DIR_NAME, "000"
        )
        tc_setup_dest_dir = os.path.join(
            self.__env_public_dir, f"apps/testbenches/", "000"
        )
        if not os.path.exists(tc_setup_dest_dir):
            shutil.copytree(tc_setup_src_dir, tc_setup_dest_dir)

        # Copy group files
        rel_path = "middleware/src/kernel/smartos/msp430f5529/"
        for src in TEST_GROUP_SRC_FILES:
            for file in glob.glob(os.path.join(group_src_dir, rel_path, src)):
                dest_dir = os.path.join(self.__env_group_dir, rel_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                try:
                    shutil.copy(
                        file,
                        dest_dir,
                    )
                except OSError as ex:
                    logging.error(ex)

    @property
    def path(self) -> str:
        """
        Returns the path to this environment directory.
        """
        return self.__env_dir

    @property
    def group_path(self) -> str:
        """
        Returns the path to the group directory of this environment.
        """
        return self.__env_group_dir

    @property
    def public_path(self) -> str:
        """
        Returns the path to the public directory of this environment.
        """
        return self.__env_public_dir

    @property
    def group_name(self) -> str:
        """
        Returns the group name that is loaded in this environment.
        """
        return self.__group_name

    @property
    def commit_hash(self) -> str:
        """
        Returns the hash of the tested commit.
        """
        return self.__commit

    @property
    def commit_hash_short(self) -> str:
        """
        Returns the short hash (first 8 chars) of the tested commit.
        """
        return self.commit_hash[0:8]

    @property
    def commit_msg(self) -> str:
        """
        Returns the commit message of the tested commit.
        """
        return self.__commit_msg

    @property
    def commit_time(self) -> int:
        """
        Returns the commit timestamp as unix millis of the tested commit.
        """
        return self.__commit_time

    def export(self, dest: str):
        """
        Copies the test environment to a given destination.

        :param dest: Path to destination.
        """
        try:
            if not os.path.exists(dest):
                shutil.copytree(self.__env_dir, dest)
            else:
                logging.error(f"Test environment export path {dest} already exists.")
        except Exception as ex:
            logging.error(f"Exporting test environment failed.", exc_info=ex)

    def cleanup(self):
        """
        Cleanup the test environment and remove directories used for testing.
        """
        try:
            if os.path.exists(self.__env_dir):
                shutil.rmtree(self.__env_dir)
            else:
                logging.error(
                    f"Could not cleanup test environment because test environment does"
                    f" not exist."
                )
        except Exception as ex:
            logging.error(f"Failed to clean test environment. {ex}")


def get_expected_test_case_output(test_case_name: str) -> str:
    conf = get_config()
    file = os.path.join(
        conf.tc_root_path, TEST_OUTPUT_DIR_NAME, test_case_name + ".txt"
    )
    with open(file, "r") as f:
        return f.read()


def get_test_case_definitions() -> str:
    conf = get_config()
    path = os.path.join(conf.tc_root_path, TEST_DEFINITION_FILE)
    with open(path, "r") as f:
        return f.read()


def _create_msp_identifier_program(template, device_id) -> str:
    template = f"#define {MSP_ID_GENERATOR_DEFINE}\n" + template
    program = template.replace(MSP_ID_DEVICE_ID_TEMPLATE, hex(device_id))
    return program


def create_msp430_identifier_program(device_id: int) -> str:
    """
    Create a new MSP430 identification program.

    :param device_id: The device id to use for the new program.

    :returns: Path to the program file.
    """
    with open(os.path.join(MSP_ID_IDENTIFIER_PATH, "main.c"), "r") as f:
        template = f.read()
    program = _create_msp_identifier_program(template, device_id)
    cid = hex(device_id).replace("0x", "")
    file = f"_main_{cid}.c"
    path = os.path.join(MSP_ID_IDENTIFIER_PATH, file)
    with open(path, "w") as f:
        f.write(program)
    return file


def get_public_repo_name() -> str:
    conf = get_config()
    name = GIT_PUBLIC_NAME_TEMPLATE.format(conf.term)
    return name


def _clear_directory(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


def _get_local_git_root() -> str:
    if not os.path.exists(GIT_LOCAL_ROOT_DIR):
        os.mkdir(GIT_LOCAL_ROOT_DIR)
    return GIT_LOCAL_ROOT_DIR


def _get_local_public_git_directory() -> str:
    git_local = _get_local_git_root()
    return os.path.join(git_local, get_public_repo_name())


def _get_local_group_git_directory(group_name: str) -> str:
    git_local = _get_local_git_root()
    return os.path.join(git_local, "groups", group_name)


def _get_local_sys_git_directory() -> str:
    git_local = _get_local_git_root()
    return os.path.join(git_local, "sys")


def _get_rel_remote_group_directory(group_name: str) -> str:
    conf = get_config()
    return conf.git_student_path.strip("/") + "/" + group_name


def _get_test_env_root() -> str:
    if not os.path.exists(TEST_ENVIRONMENT_DIRECTORY):
        os.mkdir(TEST_ENVIRONMENT_DIRECTORY)
    return TEST_ENVIRONMENT_DIRECTORY


def _get_test_env_dir(env_id: str) -> str:
    env_root = _get_test_env_root()
    return os.path.join(env_root, env_id)


def _get_test_env_group_dir(env_id: str, group_name: str) -> str:
    return os.path.join(_get_test_env_dir(env_id), group_name)


def _get_test_env_public_dir(env_id: str) -> str:
    return os.path.join(_get_test_env_dir(env_id), get_public_repo_name())


def _git_changed(repo: git.Repo) -> bool:  # type: ignore
    git_status = repo.git.status("-u")
    return (
        "Untracked files:" in git_status
        or "Changes not staged for commit:" in git_status
    )


def _load_repo(local_path: str, rel_remote_path) -> str:
    conf = get_config()

    try:
        if not os.path.exists(local_path):
            url = utils.url_builder(conf.git_server, rel_remote_path)
            logging.info(f"Clone repo {url} to {local_path}.")
            git.Repo.clone_from(url, local_path)  # type: ignore

        repo = git.Repo(local_path)  # type: ignore
    except git.GitCommandError as ex:
        logging.debug(f"Git stderr: {ex.stderr}")
        raise GitError(f"Loading repo {rel_remote_path} failed. {ex.stdout}")

    repo.git.fetch()
    repo.git.fetch("--tags", "--force")
    missing_primary = True
    for ref in repo.references:
        if ref.name == conf.git_primary_branch_name:
            missing_primary = False
            break
    if missing_primary:
        raise GitError(
            f"Repository {rel_remote_path} has no"
            f" '{conf.git_primary_branch_name}' branch."
        )
    repo.git.checkout(conf.git_primary_branch_name)
    repo.git.pull()
    return repo.heads[conf.git_primary_branch_name].commit.hexsha


def _git_handler(func, *args):
    global _git_lock
    last_error = ""
    for i in range(0, GIT_RETRIES):
        try:
            with _git_lock:
                return func(*args)
        except git.GitCommandError as ex:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            logging.info(ex)
            last_error = ex.stderr.strip("\n")
            sleep_time = random.uniform(5, 20)
            logging.debug(ex.stderr)
            logging.warning(
                f"Git command failed. This is the {i + 1}. try of function"
                f" {func.__name__}. Retry in {np.round(sleep_time, 1)}s for "
                f" {GIT_RETRIES - 1 - i} more times."
            )
            time.sleep(sleep_time)
    raise GitError(
        f"Git interface function {func.__name__} failed too often with error:"
        f" {last_error}"
    )


def init_fs():
    """
    Cleans and initializes local directories.
    """
    logging.info("Initialize filesystem.")
    git_local = _get_local_git_root()
    env_root = _get_test_env_root()
    _clear_directory(git_local)
    _clear_directory(env_root)


def load_repo(local_path: str, rel_remote_path: str) -> str:
    """
    Initializes and updates a local clone.

    :param local_path: Local git repository path.
    :param rel_remote_path: Relative path on git server.
    :returns: Hash of latest commit on primary branch.
    """
    return _git_handler(_load_repo, local_path, rel_remote_path)


def load_group(group_name: str) -> str | None:
    """
    Initializes and updates a local clone for the group.

    :raises GitError: If cloning or pulling the group repository failed.

    :param group_name: Repo name.
    :returns: Hash of latest commit on primary branch.
    """
    rel_remote_path = _get_rel_remote_group_directory(group_name)
    local_path = _get_local_group_git_directory(group_name)
    return load_repo(local_path, rel_remote_path)


def load_public() -> str:
    """
    Initializes and updates the local RTOS repository.

    :raises GitError: If cloning or pulling the public repository failed.

    :returns: Hash of lates commit on primary branch.
    """
    global _public_repo_timestamp, _public_repo_commit
    if time.time() - _public_repo_timestamp < GIT_PUBLIC_CACHE_TIME_S:
        return _public_repo_commit
    conf = get_config()
    local_path = _get_local_public_git_directory()
    rel_remote_path = os.path.join(
        conf.git_public_path, GIT_PUBLIC_NAME_TEMPLATE.format(conf.term)
    )
    _public_repo_commit = load_repo(local_path, rel_remote_path)
    _public_repo_timestamp = time.time()
    return _public_repo_commit


def _get_next_commit(group_name: str, commit: str | None = None) -> str:
    conf = get_config()
    git_dir = _get_local_group_git_directory(group_name)
    repo = git.Repo(git_dir)  # type: ignore
    tmp_commit = repo.head.commit.hexsha
    repo.git.checkout(conf.git_primary_branch_name)
    commit_list = list(repo.iter_commits(reverse=True))
    assert len(commit_list) > 0
    found_commit = False
    next_commit = commit_list[0].hexsha
    for c in commit_list:
        if c.hexsha == commit:
            found_commit = True
            next_commit = c.hexsha
        elif found_commit:
            next_commit = c.hexsha
            break
    repo.git.checkout(tmp_commit)
    return next_commit


def _get_latest_commit(group_name: str) -> str:
    conf = get_config()
    git_dir = _get_local_group_git_directory(group_name)
    repo = git.Repo(git_dir)  # type: ignore
    tmp_commit = repo.head.commit.hexsha
    repo.git.checkout(conf.git_primary_branch_name)
    latest_commit = repo.head.commit.hexsha
    repo.git.checkout(tmp_commit)
    return latest_commit


def get_next_commit(group_name: str, commit: str | None = None) -> str:
    """
    Get the next child commit on the primary branch after the provided commit.
    If no commit is provided or the commit is not found in the primary branch,
    the first one will be used.

    :param group_name: Group name for repository.
    :param state: The commit hash of the parent.

    :returns: Returns the hash of the child commit on the primary branch.
    """
    return _git_handler(_get_next_commit, group_name, commit)


def get_latest_commit(group_name: str) -> str:
    """
    Get the latest commit on the primary branch.

    :param group_name: Group name for repository.

    :returns: Returns the hash of the commit.
    """
    return _git_handler(_get_latest_commit, group_name)


def _get_commit_message(group_name: str, commit: str) -> str:
    git_dir = _get_local_group_git_directory(group_name)
    repo = git.Repo(git_dir)  # type: ignore
    repo.git.checkout(commit)
    message: str = repo.head.commit.message  # type: ignore
    return message


def get_commit_message(group_name: str, commit: str) -> str:
    """
    Get the message from a specific commit.

    :param group_name: Group name for repository.
    :param commit: The commit hash from where to get the message.

    :returns: Returns the commit message.
    """
    return _git_handler(_get_commit_message, group_name, commit)


def _get_commit_timestamp(group_name: str, commit: str) -> int:
    git_dir = _get_local_group_git_directory(group_name)
    repo = git.Repo(git_dir)  # type: ignore
    repo.git.checkout(commit)
    timestamp = repo.head.commit.committed_date * 1000
    return timestamp


def get_commit_timestamp(group_name: str, commit: str) -> int:
    """
    Get the timestamp from a specific commit.

    :param group_name: Group name for repository.
    :param commit: The commit hash from where to get the timestamp.

    :returns: Returns the commit timestamp as unix millis.
    """
    return _git_handler(_get_commit_timestamp, group_name, commit)


def _setup_test_env(group_name: str, git_state: str) -> TestEnv:
    return TestEnv(group_name, git_state)


def setup_test_env(group_name: str, commit: str) -> TestEnv:
    """
    Creates a save environment for the test run. This is outside of the local git
    repositories.
    """
    return _git_handler(_setup_test_env, group_name, commit)


def load_test_case(test_env: TestEnv, test_case_name: str) -> str:
    """
    Load a given test case into the test environment.

    :raises TestCaseError: If loading the test case failed.

    :param env_id: A test environment.
    :param test_case_name: Name of test case that should be loaded.

    :returns: Path to the loaded test case.
    """
    # Create a repository copy for this test case
    tc_env_dir = os.path.join(test_env.path, test_case_name)
    tc_env_public = os.path.join(
        tc_env_dir, test_env.public_path.replace(test_env.path, "").strip("/")
    )
    tc_env_group = os.path.join(
        tc_env_dir, test_env.group_path.replace(test_env.path, "").strip("/")
    )

    if not os.path.exists(tc_env_public):
        shutil.copytree(test_env.public_path, tc_env_public)

    if not os.path.exists(tc_env_group):
        shutil.copytree(test_env.group_path, tc_env_group)

    conf = get_config()
    src_dir = os.path.join(conf.tc_root_path, TEST_TESTBENCHE_DIR_NAME)
    dest_dir = os.path.join(tc_env_public, f"apps/testbenches/")
    tc_src_dir = os.path.join(src_dir, test_case_name)
    tc_dest_dir = os.path.join(dest_dir, test_case_name)

    if not os.path.exists(tc_src_dir):
        raise TestCaseError(
            f"Could not find source directory {tc_src_dir} for test case"
            f" {test_case_name}."
        )

    # Copy test case
    if os.path.exists(tc_dest_dir):
        shutil.rmtree(tc_dest_dir)
    shutil.copytree(tc_src_dir, tc_dest_dir)

    for header_file in TEST_HEADER_FILES:
        shutil.copyfile(
            os.path.join(src_dir, header_file), os.path.join(dest_dir, header_file)
        )

    return tc_dest_dir


def _publish_test_run_report(
    group_name: str, commit: str, content: str, file_type: str = "md"
):
    logging.info(f"Publish test run report for {group_name}.")
    conf = get_config()
    local_sys_dir = _get_local_sys_git_directory()
    _load_repo(local_sys_dir, conf.git_system_path)
    repo = git.Repo(local_sys_dir)  # type: ignore
    repo.git.checkout(conf.git_primary_branch_name)
    report_file_dir = os.path.join(local_sys_dir, "reports", group_name)
    if not os.path.exists(report_file_dir):
        os.makedirs(report_file_dir)
    report_file = os.path.join(report_file_dir, f"README.{file_type}")
    with open(report_file, "w") as f:
        f.write(content)

    if _git_changed(repo):
        repo.git.add("*")
        repo.git.commit(m=f"Test Report {group_name} {commit[0:8]}")
        repo.git.push()


def publish_test_run_report(
    group_name: str, commit: str, content: str, file_type: str = "md"
):
    """
    Publish a test run report for a specific group.

    :param group_name: Group name for repository.
    :param content: The content of the report.
    :param file_type: The file type of the content.
    """
    _git_handler(_publish_test_run_report, group_name, commit, content, file_type)


def _guarantee_remote_branch(repo: git.Repo, branch_name: str):  # type: ignore
    found = False
    for ref in repo.references:
        if branch_name == ref.name.replace("origin/", ""):
            found = True
            break
    if not found:
        repo.git.checkout(b=branch_name)
        repo.git.push("--set-upstream", "origin", branch_name)


def _publish_group_report(
    group_name: str, commit: str, content: str, file_type: str = "md"
):
    logging.info(f"Publish group report for {group_name}.")
    local_group_dir = _get_local_group_git_directory(group_name)
    rel_remote_path = _get_rel_remote_group_directory(group_name)
    _load_repo(local_group_dir, rel_remote_path)
    repo = git.Repo(local_group_dir)  # type: ignore
    _guarantee_remote_branch(repo, GIT_RESULT_BRANCH_NAME)
    repo.git.checkout(GIT_RESULT_BRANCH_NAME)
    repo.git.pull("origin", GIT_RESULT_BRANCH_NAME)
    report_file_dir = os.path.join(local_group_dir, "reports")
    if not os.path.exists(report_file_dir):
        os.makedirs(report_file_dir)
    report_file = os.path.join(report_file_dir, f"README.{file_type}")
    with open(report_file, "w") as f:
        f.write(content)

    if _git_changed(repo):
        repo.git.add("*")
        repo.git.commit(m=f"Test Report {commit[0:8]}")
        repo.git.push()


def publish_group_report(
    group_name: str, commit: str, content: str, file_type: str = "md"
):
    """
    Publish test results for a specific group.

    :param group_name: Group for which to publish the report.
    :param content: The content of the report.
    :param file_type: The file type of the content.
    """
    _git_handler(_publish_group_report, group_name, commit, content, file_type)


def _publish_system_status_report(sys_report: str):
    logging.info(f"Publish system status report.")
    conf = get_config()
    local_sys_dir = _get_local_sys_git_directory()
    _load_repo(local_sys_dir, conf.git_system_path)
    repo = git.Repo(local_sys_dir)  # type: ignore
    repo.git.checkout(conf.git_primary_branch_name)
    sys_report_file = os.path.join(local_sys_dir, f"README.md")
    with open(sys_report_file, "w") as f:
        f.write(sys_report)

    if _git_changed(repo):
        repo.git.add("*")
        repo.git.commit(m=f"Update system report")
        repo.git.push()


def publish_system_status_report(sys_report: str):
    """
    Publish the global system status report.

    :param sys_report: The content of the report.
    """
    _git_handler(_publish_system_status_report, sys_report)


def _get_tagged_group_commit(group_name: str, tags: list[str]) -> list[str]:
    lc_tags = [t.lower() for t in tags]
    git_dir = _get_local_group_git_directory(group_name)
    repo = git.Repo(git_dir)  # type: ignore
    commits: list[str] = []
    for t in repo.tags:
        if t.name.lower() in lc_tags:  # type: ignore
            commits.append(t.commit.hexsha)
    return commits


def get_tagged_group_commit(group_name: str, tags: list[str]) -> list[str]:
    """
    Get all commits tagged with one of the provided tags.

    :param group_name: The name of the group where to look for tagged commits.
    :param tags: A list of tags.

    :returns: Returns a list of commit hashes.
    """
    return _git_handler(_get_tagged_group_commit, group_name, tags)
