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
import git
import json
import shutil
import distutils.dir_util
import time
import tqdm
import logging
import argparse
import traceback
import threading
import numpy as np
import matplotlib.pyplot as plt
import testsystem.utils as tsutil
import test_framework as tf
import testsystem.filesystem as fs
import testsystem.constants as const
import testsystem.models as models

WORKING_DIR_PATH = "./_tmp"
LOG_FILE_NAME = "rtos-util.log"

_run_group_test_cnt = 0
_run_group_test_max = 0
_run_group_test_lock = threading.Lock()

_fs_lock = threading.Lock()


class TestCase:
    def __init__(self, expected_result: int, repo_data) -> None:
        self.expected_result = expected_result
        self.repo_data = repo_data


class GroupResult:
    def __init__(
        self, result: int, timestamp: float, commit: str | None = None
    ) -> None:
        self.result = result
        self.timestamp = timestamp
        self.commit = commit

    @property
    def timestamp_str(self):
        return tsutil.to_local_time_str(self.timestamp * 1000)


class TimelineCommit:
    def __init__(self, **kwargs) -> None:
        self.src_hash: str | None = None
        self.timestamp: int | None = None
        self.result: float | None = None

        for key, value in kwargs.items():
            if key == "src_hash":
                self.src_hash = value
            elif key == "timestamp":
                self.timestamp = value
            elif key == "result":
                self.result = value


class Timeline:
    def __init__(self, **kwargs) -> None:
        self.group_name: str | None = None
        self.commits: list[TimelineCommit] = []

        for key, value in kwargs.items():
            if key == "group_name":
                self.group_name = value
            elif key == "commits":
                for tc in value:
                    self.commits.append(TimelineCommit(**tc))


class TestCaseLog:
    def __init__(self, **kwargs) -> None:
        self.group_name = kwargs.get("group_name")
        self.src_commit = kwargs.get("src_commit")
        self.commit = kwargs.get("commit")
        self.commit_timestamp = kwargs.get("commit_timestamp")
        self.result_timestamp = kwargs.get("result_timestamp")
        self.expected_result = kwargs.get("expected_result")
        self.actual_result = kwargs.get("actual_result")


class TestCaseLogSet:
    def __init__(self, **kwargs) -> None:
        self.logs: list[TestCaseLog] = []

        for key, value in kwargs.items():
            if key == "logs":
                for v in value:
                    self.logs.append(TestCaseLog(**v))


test_logs = TestCaseLogSet()
test_log_lock = threading.Lock()


def _get_working_dir() -> str:
    global _fs_lock
    with _fs_lock:
        if not os.path.exists(WORKING_DIR_PATH):
            os.mkdir(WORKING_DIR_PATH)
        return WORKING_DIR_PATH


def _clean_working_dir():
    global _fs_lock
    with _fs_lock:
        if os.path.exists(WORKING_DIR_PATH):
            shutil.rmtree(WORKING_DIR_PATH)


def _get_report_commits(repo: git.Repo) -> list[str]:
    """
    Get a list of all report commits from an old student repo.
    """
    branch_name = "testresults"
    logging.info(f"Checkout branch {branch_name}")
    repo.git.checkout(branch_name)
    commit_list = list(repo.iter_commits(reverse=True))
    logging.info(f"Found {len(commit_list)} commits on branch {branch_name}.")
    result_commits = []
    for commit in commit_list:
        if commit.message.startswith("new test results:"):
            result_commits.append(commit.hexsha)
    logging.info(f"Found {len(result_commits)} testresults.")
    return result_commits


def _get_expected_result(repo: git.Repo, result_commit: str) -> tuple[int, float, str]:
    """
    Get the expected result and the corresponding srouce commit from an old student repo
    results commit.
    """
    repo.git.checkout(result_commit)
    data_dir = os.path.join(repo.working_tree_dir, "testreports/logData")
    file = None
    for item in os.scandir(data_dir):
        file = os.path.join(data_dir, item)
        if os.path.isfile(file):
            break
    assert file is not None
    with open(file, "r") as f:
        raw_content = f.read()
    lines = raw_content.splitlines()
    line = lines[-1]
    if len(line) == 0:
        line = lines[-2]
    line = line[21:-2]
    data = json.loads(line)
    result = 0
    commit_hash = None
    timestamp = repo.head.commit.committed_date
    for ex in data:
        ex_data = data[ex]
        for tc in ex_data:
            if commit_hash is None and len(tc["sha1id"]) > 0:
                commit_hash = tc["sha1id"]
            if not tc["size"] and not tc["timing"] and int(tc["id"]) > 0:
                result += tc["result"]
    assert commit_hash is not None
    return int(result), timestamp, commit_hash


def _export_result_as_test_case(
    dest: str, repo: git.Repo, result: GroupResult, prefix: str = ""
):
    try:
        repo.git.checkout(result.commit)
        src_path = repo.working_tree_dir
        dest_commit_dir = os.path.join(dest, result.commit)
        dest_data = os.path.join(dest_commit_dir, "data")
        result_file = os.path.join(dest_commit_dir, "result.json")
        global _fs_lock
        with _fs_lock:
            if os.path.exists(dest_commit_dir):
                shutil.rmtree(dest_commit_dir)
            os.mkdir(dest_commit_dir)
        shutil.copytree(src_path, dest_data)
        dest_git_dir = os.path.join(dest_data, ".git")
        shutil.rmtree(dest_git_dir)
        report = tf.ExpectedResult(total=result.result)
        with open(result_file, "w") as f:
            json.dump(report.__dict__, f, indent=4)
    except git.GitCommandError as ex:
        logging.error(f"Failed to export result as test case. {ex.stderr}")


def get_group_results(
    repo: git.Repo, start_tag_name: str | None = None, exit_tag_name: str | None = None
) -> list[GroupResult]:
    if start_tag_name is not None:
        logging.info(f"Use start tag: {start_tag_name}")
    if exit_tag_name is not None:
        logging.info(f"Use exit tag: {exit_tag_name}")

    result_commits = _get_report_commits(repo)

    # Find start end exit commits
    exit_commit = None
    start_commit = None
    for tag in repo.tags:
        if start_tag_name is not None and tag.name == start_tag_name:
            start_commit = tag.commit.hexsha
            logging.info(f"Found start commit: {start_commit}")
        if exit_tag_name is not None and tag.name == exit_tag_name:
            exit_commit = tag.commit.hexsha
            logging.info(f"Found exit commit: {exit_commit}")
    if exit_tag_name is not None and exit_commit is None:
        logging.warning(f"No commit found for exit tag '{exit_tag_name}'.")
    if start_tag_name is not None and start_commit is None:
        logging.warning(f"No commit found for start tag '{start_tag_name}'.")

    test_results = {}
    started = start_tag_name is None
    for result_commit in result_commits:
        result, timestamp, commit_hash = _get_expected_result(repo, result_commit)
        if not started or start_commit == commit_hash:
            if start_commit == commit_hash:
                started = True
            continue
        group_result = GroupResult(result, timestamp, commit_hash)
        if commit_hash in test_results and test_results[commit_hash].result != result:
            logging.warning(
                f"Test results for commit {commit_hash} do not match (Result1 ="
                f" {test_results[commit_hash].result} at"
                f" {test_results[commit_hash].timestamp_str}, Result2 = {result} at"
                f" {group_result.timestamp_str}). Is this a racing condition?"
            )
        test_results[commit_hash] = group_result
        if exit_commit is not None and commit_hash == exit_commit:
            logging.info(f"Stop processing. Exit tag reached.")
            break
    group_results = list(test_results.values())
    logging.info(f"Found {len(group_results)} unique test results.")
    return group_results


def generate_group_tc(
    src: str, dest: str, starttag: str | None = None, exittag: str | None = None
):
    logging.info("Generate test cases")
    wd = _get_working_dir()
    name = src.split("/")[-1].split(".")[0]
    logging.info(f"Group name: {name}")
    src_dir = os.path.join(wd, name)
    logging.info(f"Clone source repository {src}")
    repo = git.Repo.clone_from(src, src_dir)
    group_results = get_group_results(
        repo, start_tag_name=starttag, exit_tag_name=exittag
    )
    logging.info(f"Start exporting {len(group_results)} results as test cases.")
    if dest is None:
        dest = "./gen-out"
        logging.info(f"No destination provided. Using default destination '{dest}'.")
    global _fs_lock
    with _fs_lock:
        if not os.path.exists(dest):
            os.mkdir(dest)
    tl_commits = []
    with tqdm.tqdm(total=len(group_results), ncols=64) as pbar:
        for group_result in group_results:
            _export_result_as_test_case(dest, repo, group_result, prefix=f"{name} ")
            tl_commits.append(
                TimelineCommit(
                    src_hash=group_result.commit,
                    timestamp=group_result.timestamp,
                    result=group_result.result,
                ).__dict__
            )
            pbar.update()
    logging.info("Export commit timeline.")
    timeline = {"name": name, "commits": tl_commits}
    timeline_file = os.path.join(dest, "timeline.json")
    with open(timeline_file, "w") as f:
        json.dump(timeline, f, indent=4)
    logging.info("Export finished.")


def generate(args):
    if args.term is not None:
        r_start = 1
        r_end = 100
        if args.range is not None:
            r_start, r_end = args.range
        dest_dir = "tc-" + args.term if args.dest is None else args.dest
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
        logging.info(f"Generate test cases from term {args.term}.")
        failed_groups = []
        for nr in range(r_start, r_end):
            group_name = models.Group.get_name(nr, args.term)
            src = args.src + "/" + group_name + ".git"
            dest = dest_dir + "/" + group_name
            try:
                generate_group_tc(src, dest, args.starttag, args.exittag)
            except:
                failed_groups.append(group_name)

        if len(failed_groups) > 0:
            logging.info(f"Failed groups:")
            for failed_group in failed_groups:
                logging.info(f"   {failed_group}")
    else:
        generate_group_tc(args.src, args.dest, args.starttag, args.exittag)


def plot_result_stats(args):
    logging.info("Visualize results from group.")
    wd = _get_working_dir()
    name = args.src.split("/")[-1].split(".")[0]
    logging.info(f"Group name: {name}")
    src_dir = os.path.join(wd, name)
    logging.info(f"Clone source repository {args.src}")
    repo = git.Repo.clone_from(args.src, src_dir)
    group_results = get_group_results(
        repo, start_tag_name=args.starttag, exit_tag_name=args.exittag
    )
    size = len(group_results)
    points = np.zeros(size)
    timestamps = np.zeros(size)
    for i in range(0, size):
        points[i] = group_results[i].result
        timestamps[i] = group_results[i].timestamp
        logging.info(
            f"Result: {group_results[i].result} | Timestamp:"
            f" {group_results[i].timestamp_str} | Commit: {group_results[i].commit}"
        )
    plt.plot(timestamps, points)
    plt.grid(True)
    plt.show()


def _wait_for_report(repo: git.Repo, result_commit_hash: str) -> tf.DetailedGroupResult:
    while True:
        try:
            repo.git.fetch()
            repo.git.checkout(const.GIT_RESULT_BRANCH_NAME)
            repo.git.pull()
            commit_list = list(repo.iter_commits(reverse=True))
            for c in commit_list:
                repo.git.checkout(c.hexsha)
                report_path = os.path.join(repo.working_dir, "reports", "README.md")  # type: ignore
                if not os.path.exists(report_path):
                    continue
                with open(report_path, "r") as f:
                    content = f.read()
                result = tf.parse_group_report(content)
                if (
                    result is not None
                    and result.tested_commit[0:8] == result_commit_hash[0:8]
                ):
                    return result
        except git.GitCommandError as ex:
            logging.debug(f"Wait for report threw git command error. Continue waiting.")
        time.sleep(10)


def _save_logs():
    global test_logs, test_log_lock
    with test_log_lock:
        log_array = []
        for l in test_logs.logs:
            log_array.append(l.__dict__)
        with open(LOG_FILE_NAME, "w") as f:
            json.dump({"logs": log_array}, f, indent=4)


def _run_group_test(timeline: Timeline, group_src_dir: str, group_repo_path: str):
    global _run_group_test_cnt, _run_group_test_max, _run_group_test_lock
    with _run_group_test_lock:
        _run_group_test_max += len(timeline.commits)
    group_name = group_repo_path.split("/")[-1].split(".")[0]
    try:
        logging.info(
            f"[{group_name}] Start test execution. Source: {group_src_dir} |"
            f" Repository: {group_repo_path}"
        )
        local_repo_path = os.path.join(_get_working_dir(), "git", group_name)
        if os.path.exists(local_repo_path):
            shutil.rmtree(local_repo_path)
        os.makedirs(local_repo_path)
        repo = git.Repo.clone_from(group_repo_path, local_repo_path)
        for tl_commit in timeline.commits:
            try:
                with _run_group_test_lock:
                    _run_group_test_cnt += 1
                with _run_group_test_lock:
                    progress_str = f"{_run_group_test_cnt}/{_run_group_test_max}"
                prefix_str = f"[{progress_str}] [{group_name}]"
                repo.git.checkout("main")
                log = TestCaseLog(
                    group_name=group_name,
                    src_commit=tl_commit.src_hash,
                    expected_result=tl_commit.result,
                )
                # Commit data
                data_dir = os.path.join(group_src_dir, tl_commit.src_hash, "data")
                distutils.dir_util.copy_tree(data_dir, local_repo_path)
                if fs._git_changed(repo):
                    repo.git.add("*")
                    repo.git.commit(m="RTOS Util test commit")
                    commit_hash = repo.head.commit.hexsha
                    log.commit = commit_hash
                    log.commit_timestamp = time.time()
                    hash_info_str = (
                        f"Commit: {commit_hash[0:8]} | Source:"
                        f" {tl_commit.src_hash[0:8]}"
                    )
                    logging.info(f"{prefix_str} Create new commit. {hash_info_str}")
                    while True:
                        try:
                            repo.git.push()
                            break
                        except git.GitCommandError:
                            logging.debug("Failed to push commit. Retry in 10 seconds.")
                            time.sleep(10)
                else:
                    logging.info(
                        f"{prefix_str} Noting changed from last commit. Continue."
                    )
                    continue
                # Wait for test system report
                logging.info(f"{prefix_str} Wait for results report. {hash_info_str}")
                report = _wait_for_report(repo, commit_hash)
                log.result_timestamp = time.time()
                log.actual_result = report.total
                global test_log_lock, test_logs
                with test_log_lock:
                    test_logs.logs.append(log)
                _save_logs()
                repo.git.checkout("main")
                logging.info(
                    f"{prefix_str} Received result report with {report.total} points."
                    f" {hash_info_str}"
                )
                # Check report result
                if report.total != tl_commit.result:
                    logging.warning(
                        f"{prefix_str} Expected {tl_commit.result} points for this"
                        f" commit but got {report.total} from the test system."
                    )
                else:
                    logging.info(
                        f"{prefix_str} Actual result with {report.total} points meets"
                        " the expectations. Test case was successful."
                    )
            except git.GitCommandError as ex:
                logging.warning("Git command error. Continue anyway...", exc_info=ex)
    except:
        # traceback.print_exc()
        logging.error("Group test thread failed.")
    logging.info(f"[{group_name}] Test execution finished.")


def run_group_tests(groups):
    logging.info(f"Start test run with {len(groups)} groups.")
    logging.info("Load group timelines.")
    test_groups = {}
    for group in groups:
        test_group = {}
        group_dir = group[0]
        test_group["group_dir"] = group_dir
        test_group["repo_path"] = group[1]
        timeline_file = os.path.join(group_dir, "timeline.json")
        if not os.path.exists(timeline_file):
            logging.warning(
                f"No timeline file found in directory {group_dir}. This group will not"
                " be used for testing."
            )
            continue
        with open(timeline_file, "r") as f:
            json_obj = json.load(f)
            timeline = Timeline(**json_obj)
            test_group["timeline"] = timeline
        test_groups[group_dir] = test_group
    logging.info(f"Found {len(test_groups)} groups with valid timeline files.")
    threads = []
    for test_group in test_groups.values():
        thread = threading.Thread(
            target=_run_group_test,
            args=(
                test_group["timeline"],
                test_group["group_dir"],
                test_group["repo_path"],
            ),
        )
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


def run_test(args):
    if args.g is not None:
        run_group_tests(args.g)
    else:
        if args.src is None:
            logging.critical("Missing Argument. Set the test case source with -s.")
        if args.term is None:
            logging.critical("Missing Argument. Set the term with -t.")
        if args.remote is None:
            logging.critical("Missing Argument. Set the git remote path with -r.")
        logging.info(f"Run group tests for term {args.term}.")
        groups = []
        src_group_dirs = os.listdir(args.src)
        for nr in range(1, 100):
            src_group_name = None
            for src_group_dir in src_group_dirs:
                if src_group_dir.endswith(f"{nr:02}"):
                    src_group_name = src_group_dir
                    break
            if not src_group_name:
                continue
            group_name = models.Group.get_name(nr, args.term)
            group = [
                args.src + "/" + src_group_name,
                args.remote + "/" + group_name + ".git",
            ]
            groups.append(group)
        run_group_tests(groups)


def analyze_logs(args):
    json_files = args.files
    log_sets: list[TestCaseLogSet] = []
    for json_file in json_files:
        with open(json_file, "r") as f:
            data = json.load(f)
            tc_log_set = TestCaseLogSet(**data)
            log_sets.append(tc_log_set)

    commit_map = {}
    for log_set in log_sets:
        for log in log_set.logs:
            if log.src_commit not in commit_map:
                commit_map[log.src_commit] = []
            commit_map[log.src_commit].append(log)

    d_time_max = 0
    d_time_min = 9999999
    d_time_sum = 0
    log_cnt = 0
    success_cnt = 0
    expected_sum = 0
    diff_sum = 0
    for commit in commit_map:
        logs: list[TestCaseLog] = commit_map[commit]
        failed_tests: list[TestCaseLog] = []
        for log in logs:
            assert log.result_timestamp is not None
            assert log.expected_result is not None

            log_cnt += 1

            d_time = log.result_timestamp - log.commit_timestamp
            d_time_sum += d_time
            if d_time > d_time_max:
                d_time_max = d_time
            if d_time < d_time_min:
                d_time_min = d_time

            if log.expected_result != log.actual_result:
                diff_sum += abs(log.expected_result - log.actual_result)
                failed_tests.append(log)
            else:
                success_cnt += 1

            expected_sum += log.expected_result
        if len(failed_tests) == 0:
            logging.info(
                f"[{logs[0].group_name}] [{commit[0:8]}] All {len(logs)} tests"
                " successful."
            )
        else:
            actual_results = ", ".join([str(r.actual_result) for r in failed_tests])
            logging.info(
                f"[{logs[0].group_name}] [{commit[0:8]}] {len(failed_tests)} of"
                f" {len(logs)} tests did not match the expected result"
                f" {logs[0].expected_result}. Actual results: {actual_results}"
            )

    logging.info(
        f"Waiting times | Min: {int(d_time_min)}s Max: {int(d_time_max)}s Avg:"
        f" {int(d_time_sum / log_cnt)}s"
    )
    logging.info(f"Success rate: {np.round((1 - (diff_sum / expected_sum)) * 100, 2)}%")
    logging.info(f"{success_cnt} of {log_cnt} test cases were successful.")


if __name__ == "__main__":
    stdout_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.setLevel(level=logging.INFO)

    logging.basicConfig(level=logging.DEBUG, handlers=[stdout_handler])

    parser = argparse.ArgumentParser(
        description=(
            "This program can be used to generate and run end-to-end tests for the RTOS"
            " Testsystem."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    # gen options
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate test cases from an old student git repository.",
        aliases=["gen"],
    )
    gen_parser.add_argument(
        "src", help="The git source used to generate the test cases."
    )
    gen_parser.add_argument(
        "-o",
        dest="dest",
        help="The output directory where to write the generated test cases.",
    )
    gen_parser.add_argument(
        "-s",
        dest="starttag",
        help=(
            "Specify a start tag (exclusive). Start generation after this tag is found."
        ),
    )
    gen_parser.add_argument(
        "-e",
        dest="exittag",
        help=(
            "Specify an exit tag (inclusive). Stop generation after this tag is found."
        ),
    )
    gen_parser.add_argument(
        "-t",
        dest="term",
        help=(
            "Use this to generate test cases for all group repositories in a specific"
            " term. The src should be the root url of the group repos."
        ),
    )
    gen_parser.add_argument(
        "--range",
        nargs=2,
        type=int,
        metavar=("start", "end"),
        help="Set a range of group numbers that should be used.",
    )
    gen_parser.add_argument("--log-file", help="Set the log file destination.")
    gen_parser.set_defaults(func=generate)

    # stats options
    stats_parser = subparsers.add_parser(
        "stats", help="Analyse and visualize group stats."
    )
    stats_subparsers = stats_parser.add_subparsers(dest="type")
    result_parser = stats_subparsers.add_parser(
        "result", help="Analyse and visualize group result points."
    )
    result_parser.add_argument("src", help="The git source to analyze.")
    result_parser.add_argument(
        "-s",
        dest="starttag",
        help=(
            "Specify a start tag (exclusive). Start generation after this tag is found."
        ),
    )
    result_parser.add_argument(
        "-e",
        dest="exittag",
        help=(
            "Specify an exit tag (inclusive). Stop generation after this tag is found."
        ),
    )
    result_parser.set_defaults(func=plot_result_stats)
    log_parser = stats_subparsers.add_parser(
        "log", help="Analyse and visualize result logs."
    )
    log_parser.add_argument("-f", dest="files", nargs="+", help="Log files to analyze.")
    log_parser.set_defaults(func=analyze_logs)

    # run options
    run_parser = subparsers.add_parser(
        "run", help="Perform a test run on the test system."
    )
    run_parser.add_argument(
        "-g",
        nargs=2,
        metavar=("SRC", "REPO"),
        action="append",
        help=(
            "Register a group for the test run. This argument can be used multiple"
            " times. For each group you must specify a source directory. The source"
            " directory must contain a timeline file with the corresponding test cases."
            " To generate a test group from an existing student group repository use"
            " the 'gen' argument. Additionally an upstream repository must be"
            " provided. This is the repository where the test group will push its test"
            " cases and where it waits for reports from the testsystem. The group name"
            " in the timeline file and the name of the upstream repo do not have to"
            " match."
        ),
    )
    run_parser.add_argument(
        "-t",
        dest="term",
        help=(
            "Run test cases for a complete term. Set the source to the directory with"
            " the group test cases."
        ),
    )
    run_parser.add_argument(
        "-s", dest="src", help="The source directory for group test cases."
    )
    run_parser.add_argument(
        "-r", dest="remote", help="The root path for the remote group repositories."
    )
    run_parser.add_argument("--log-file", help="Set the log file destination.")
    run_parser.set_defaults(func=run_test)

    use_param = True
    if use_param:
        args = parser.parse_args()
    else:
        # args = parser.parse_args(
        #    ["stats", "log", "-f", "rtos-util.log.1", "rtos-util.log.2"]
        # )
        args = parser.parse_args(
            [
                "run",
                "-g",
                "tc-SS22-Group04",
                "git@iti-gitlab.tugraz.at:eas/teaching/rtos_ss23/RTOS_SS23_Group02.git",
                "-g",
                "tc-SS22-Group08",
                "git@iti-gitlab.tugraz.at:eas/teaching/rtos_ss23/RTOS_SS23_Group03.git",
                "-g",
                "tc-SS22-Group13",
                "git@iti-gitlab.tugraz.at:eas/teaching/rtos_ss23/RTOS_SS23_Group04.git",
            ]
        )

    try:
        if args.log_file is not None:
            LOG_FILE_NAME = args.log_file
    except AttributeError:
        pass

    # Rename log file if it exists
    if os.path.exists(LOG_FILE_NAME):
        max_nr = 0
        for f in os.listdir("."):
            if f.startswith(LOG_FILE_NAME + "."):
                nr = int(f.split(".")[-1])
                if nr > max_nr:
                    max_nr = nr
        os.rename(LOG_FILE_NAME, LOG_FILE_NAME + "." + str(max_nr + 1))

    _clean_working_dir()
    try:
        args.func(args)
    except:
        # _clean_working_dir()
        traceback.print_exc()
        logging.error("Command failed!")
        exit(-1)
