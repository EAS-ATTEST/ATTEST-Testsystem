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

import time
import datetime
import numpy as np
import testsystem.config as cnf
import testsystem.utils as utl
import testsystem.scheduling as scheduling
import testsystem.models.test_case_def as tcdef

from collections import defaultdict
from testsystem.models import (
    TestResult,
    Group,
    TestCaseDef,
    TestUnit,
    ConnectionInfo,
    TestSet,
)
from testsystem.constants import (
    REPORT_DISABLE_BUILD_OUTPUT,
    REPORT_DISABLE_FLASH_OUTPUT,
    EE_BAD_COMMIT_MESSAGE_TEXT,
    EE_BAD_COMMIT_MESSAGE_URL,
    EE_BAD_COMMIT_MESSAGE_ENABLED,
    EE_BAD_COMMIT_MESSAGES,
)


def _md_details_section(name: str, content: str) -> str:
    return (
        "<details>\n"
        + f'<summary markdown="span">{name}</summary>\n\n'
        + f"```\n{content}\n```\n\n"
        + "</details>\n\n"
    )


def _create_markdown_report_for_test_result(test_result: TestResult) -> str:
    unicode_cross = "&#x274c;"
    unicode_check = "&#x2705;"
    success_status = unicode_cross
    if test_result.successful:
        if test_result.evaluate:
            if test_result.evaluation_value > 0:
                success_status = unicode_check
        else:
            success_status = unicode_check

    report = f"### Test Case {test_result.test_case_id} {success_status}\n\n"
    report += f"**Result: {test_result.result}**\n\n"
    if test_result.build_output != None and not REPORT_DISABLE_BUILD_OUTPUT:
        report += _md_details_section("Build Output", test_result.build_output)
    if test_result.build_error != None:
        report += _md_details_section(f"Build Error &#x26a0;", test_result.build_error)
    if test_result.flash_output != None and not REPORT_DISABLE_FLASH_OUTPUT:
        report += _md_details_section("Flash Output", test_result.flash_output)
    if test_result.flash_error != None:
        report += _md_details_section(f"Flash Error &#x26a0;", test_result.flash_error)
    if test_result.output != None and len(test_result.output) > 0:
        report += _md_details_section(f"Program Output", test_result.output)
    return report


def create_md_report_for_test_set(test_set: TestSet) -> str:
    conf = cnf.get_config()

    group = test_set.group
    commit_hash: str = test_set.commit_hash
    commit_link = conf.get_group_commit_link(group.group_name, commit_hash)

    ex_dict = dict()
    for test_result in test_set.test_results:
        tc_def = test_result.tc_def
        if tc_def is None:
            continue
        if tc_def.exercise_nr not in ex_dict:
            ex_dict[tc_def.exercise_nr] = dict()
            ex_dict[tc_def.exercise_nr]["test_case_id"] = []
        ex_dict[tc_def.exercise_nr]["test_case_id"].append(test_result.test_case_id)
        ex_dict[tc_def.exercise_nr][test_result.test_case_id] = (
            _create_markdown_report_for_test_result(test_result)
        )

    md_result = f"# Test Results for Group {group.group_nr}\n\n"

    commit_link_name = commit_hash[0:8]
    commit_msg = test_set.commit_message.split("\n")[0]
    md_result += f"Tested Commit: [{commit_link_name}]({commit_link})<br/>"
    md_result += f"Commit Time: {utl.to_local_time_str(test_set.commit_time)}<br/>"
    if commit_msg is not None and len(commit_msg) > 0:
        md_result += f"Commit Message: {commit_msg}<br/>"
    md_result += "\n\n"

    for ex in sorted(ex_dict):
        md_result += f"## Exercise {ex}\n\n"
        for test_case_id in sorted(ex_dict[ex]["test_case_id"]):
            md_result += ex_dict[ex][test_case_id]
    return md_result


def _get_group_table(groups: list[Group], config: cnf.Config) -> str:
    md_table = "|Group Number|Priority|Latest Tested Commit|Test Results|\n"
    md_table += "|---|---:|:---:|---|\n"
    for group in groups:
        test_set = group.get_latest_finished_test_set()
        priority = np.round(group.get_priority(), 1)
        if test_set is None:
            md_table += f"|{group.group_nr}|{priority}|None|No Results|\n"
        else:
            link = config.get_group_commit_link(group.group_name, test_set.commit_hash)
            link_name: str = test_set.commit_hash[0:8]
            if len(test_set.commit_message) > 0:
                msg: str = test_set.commit_message.split("\n")[0]
                link_name += f" - {msg}"
            success_cnt = 0
            sum_cnt = 0
            for r in test_set.test_results:
                assert r.tc_def is not None
                if r.evaluate:
                    sum_cnt += 1
                    success_cnt += r.evaluation_value
            md_table += (
                f"|{group.group_nr}|{priority}|[{link_name}]({link})|[{success_cnt} of"
                f" {sum_cnt} successful](./reports/{group.group_name}/)|\n"
            )
    return md_table + "\n\n"


def _get_tests_table(test_case_defs: list[TestCaseDef]) -> str:
    md_table = (
        "|Test Case Id|Description|Exercise|Timing|Size|Panic|Ranking|Runtime / s|\n"
    )
    md_table += "|---|---|:---:|---|---|---|---|---|\n"
    for tc in test_case_defs:
        md_table += (
            f"|{tc.id}|{tc.description}|{tc.exercise_nr}|{utl.to_bool(tc.timing)}"
            + f"|{utl.to_bool(tc.size)}|{utl.to_bool(tc.panic)}|"
            + f"{utl.to_bool(tc.ranking)}|{tc.runtime}|\n"
        )
    return md_table + "\n\n"


def _get_test_unit_section(test_unit: list[TestUnit]) -> str:
    md_table = "|MSP430|PicoScope|Connections|Status|\n"
    md_table += "|---|---|---|:---:|\n"
    for tu in test_unit:
        md_msp = (
            f"Name: {tu.msp430.name}<br/>"
            + f"SN: {tu.msp430.serial_number}<br/>"
            + f"Flash Count: {tu.msp430.flash_counter}<br/>"
            + f"Ports<br/>"
            + f"- Debug: {tu.msp430.debug_port}<br/>"
            + f"- UART: {tu.msp430.uart_port}"
        )
        if tu.picoscope is not None:
            md_pico = (
                f"Name: {tu.picoscope.name}<br/>" + f"SN: {tu.picoscope.serial_number}"
            )
        else:
            md_pico = "No scope connected."
        md_cons = ""
        for con in tu.connections:
            md_cons += (
                f"Port {con.msp_port} Pin {con.msp_pin} =----= "
                + f"Channel {con.pico_channel}<br/>"
            )
        msp_con_count = 0
        for c in TestUnit.get_connections():
            if c.msp430 == tu.msp430:
                msp_con_count += 1
        con_dif = msp_con_count - len(tu.connections)
        if con_dif > 0:
            md_cons += f"<br/>{con_dif} other unused connections<br/>"
        md_status = "OK"
        if not tu.is_available():
            md_status = "Unavailable"
        md_table += f"|{md_msp}|{md_pico}|{md_cons}|{md_status}|\n"

    return md_table + "\n\n"


def create_md_system_report() -> str:
    conf = cnf.get_config()
    groups = Group.get_by_term(conf.term)
    tests = TestCaseDef.get()
    test_units = TestUnit.get()

    md_result = "# RTOS Testsystem\n\n"
    md_result += f"Timestamp: {utl.to_local_time_str(time.time() * 1000)}\n\n"
    md_result += f"Last queue size: {scheduling.queue_size()} Tasks\n\n"
    poll_interval = scheduling.poll_interval()
    if poll_interval is not None:
        md_result += f"Group poll interval: {poll_interval}s\n\n"

    md_result += f"## Test Units ({len(test_units)})\n\n"
    md_result += _get_test_unit_section(test_units)

    md_result += f"## Groups ({len(groups)})\n\n"
    md_result += _get_group_table(groups, conf)

    md_result += f"## Active Test Cases ({len(tests)})\n\n"
    md_result += _get_tests_table(tests)

    return md_result


def _format_result(result: float | None) -> float | int | None:
    if result == 0 or result == 1:
        result = int(result)
    return result


class GroupStats:
    def __init__(self, group: Group, commit: str | None = None) -> None:
        if commit is None:
            self._test_set = group.get_latest_finished_test_set()
        else:
            self._test_set = group.get_test_set(commit=commit)
        self._exercise_results = defaultdict(float)
        self._total = 0
        if self._test_set is not None:
            for result in self._test_set.test_results:
                tc_def = result.tc_def
                if tc_def is None:
                    continue
                if result.evaluate:
                    result_value = result.evaluation_value
                    self._exercise_results[tc_def.exercise_nr] += result_value
                    self._total += int(result_value)
        self._group = group

    @property
    def total(self) -> int:
        return self._total

    @property
    def group(self) -> Group:
        return self._group

    @property
    def group_name(self) -> str:
        return self._group.group_name

    @property
    def group_nr(self) -> int:
        return self._group.group_nr

    def get_exercise_result(self, exercise_nr: int) -> int:
        return int(self._exercise_results[exercise_nr])

    def get_test_case_result(self, tc_id: int) -> float | int | None:
        result = None
        if self._test_set is not None:
            for test_result in self._test_set.test_results:
                if test_result.test_case_id == tc_id:
                    result = test_result.result
        return _format_result(result)


def _create_md_group_stat_table(
    group_nr: int | None = None, commit: str | None = None
) -> tuple[str, int | None]:
    config = cnf.get_config()
    groups = Group.get_by_term(config.term)
    nr_of_exercises = tcdef.get_max_exercise_nr()
    ranking_tests = tcdef.get_ranking_tests()

    # Create table header
    md_header = "|Group|Total|"
    md_divider = "|---|---|"
    for ex_nr in range(0, nr_of_exercises + 1):
        md_header += f"ex{ex_nr}|"
        md_divider += "---|"
    for rnk_test in ranking_tests:
        md_header += f"{rnk_test.description}|"
        md_divider += "---|"
    md_result = md_header + "\n" + md_divider + "\n"

    # Get stats
    stats_array = []
    for group in groups:
        if group.group_nr == group_nr and commit is not None:
            stats_array.append(GroupStats(group, commit=commit))
        else:
            stats_array.append(GroupStats(group))

    stats_array.sort(key=lambda x: x.total, reverse=True)

    # Create table rows
    group_total = None
    for stats in stats_array:
        group_name = "???"
        if stats.group.group_nr == group_nr:
            group_name = stats.group.group_name
            group_total = stats.total
        md_result += f"|{group_name}|{stats.total}|"
        for ex_nr in range(0, nr_of_exercises + 1):
            md_result += f"{stats.get_exercise_result(ex_nr)}|"
        for rnk_test in ranking_tests:
            md_result += f"{stats.get_test_case_result(rnk_test.id)}|"
        md_result += "\n"

    return md_result, group_total


def _create_md_detailed_group_report(
    test_set: TestSet, ex_header_style: str = "##"
) -> str:
    table_header = "|Id|Test Case|Deploy Process|Result|\n"
    table_header += "|---|---|---|---|\n"
    ex_dict = dict()
    for test_result in test_set.test_results:
        tc_def = test_result.tc_def
        if tc_def is None:
            continue
        if tc_def.exercise_nr not in ex_dict:
            ex_dict[tc_def.exercise_nr] = dict()
            ex_dict[tc_def.exercise_nr]["test_case_id"] = []
        ex_dict[tc_def.exercise_nr]["test_case_id"].append(test_result.test_case_id)
        result_value = _format_result(test_result.result)
        deploy_status = "Completed" if test_result.successful else "Failed"
        table_row = (
            f"|{tc_def.id}|{tc_def.description}|{deploy_status}|{result_value}|\n"
        )
        ex_dict[tc_def.exercise_nr][test_result.test_case_id] = table_row

    md_result = ""
    for ex in sorted(ex_dict):
        md_result += f"{ex_header_style} Exercise {ex}\n\n"
        md_result += table_header
        for test_case_id in sorted(ex_dict[ex]["test_case_id"]):
            md_result += ex_dict[ex][test_case_id]

    return md_result


def _create_md_group_report_by_test_set(test_set: TestSet | None = None) -> str:
    if test_set is not None:
        report = f"# Test Results for Group {test_set.group.group_nr}\n\n"
        if (
            EE_BAD_COMMIT_MESSAGE_ENABLED
            and test_set.commit_message.lower() in EE_BAD_COMMIT_MESSAGES
        ):
            commit_msg = f"[{EE_BAD_COMMIT_MESSAGE_TEXT}]({EE_BAD_COMMIT_MESSAGE_URL})"
        else:
            commit_msg = test_set.commit_message.split("\n")[0]

        group_stat_table, group_total = _create_md_group_stat_table(
            test_set.group.group_nr, test_set.commit_hash
        )

        report += f"Tested Commit: {test_set.commit_hash}\\\n"
        report += f"Commit Message: {commit_msg}\\\n"
        report += f"Commit Timestamp: {utl.to_local_time_str(test_set.commit_time)}\\\n"
        report += f"Test Timestamp: {utl.to_local_time_str(test_set.timestamp)}\\\n"
        report += f"Total Points: {group_total}\n\n"
        report += group_stat_table
        report += "## Details\n\n"
        report += _create_md_detailed_group_report(test_set)
    else:
        group_stat_table, _ = _create_md_group_stat_table()

        report = f"# Test Results\n\n"
        report += group_stat_table
    return report


def create_md_group_report(
    test_set: TestSet | None = None,
    group: Group | None = None,
    group_nr: int | None = None,
) -> str:
    """
    This function creates a markdown group report. It contains an anonymized table of
    all groups and their scores and a detailed test result section for a specific group.
    This function requires at most one parameter.

    :param test_set: A specific test set for which to create the report.
    :param group: A specific group for which to create the report.
    :param group_nr: The group number for which to create the report.

    :returns: Returns the markdown report as string.
    """
    if test_set is None:
        if group is not None:
            test_set = group.get_latest_finished_test_set()
        elif group_nr is not None:
            conf = cnf.get_config()
            group = Group.get(group_nr, conf.term)
            if group is not None:
                test_set = group.get_latest_finished_test_set()
    return _create_md_group_report_by_test_set(test_set)
