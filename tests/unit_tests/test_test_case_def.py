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

import pytest
import unittest.mock as mock

from testsystem.models.test_case_def import TestCaseDef, get_all, get
from testsystem.config import Config
from testsystem.constants import TC_DEF_CACHE_TIME_S


@mock.patch("testsystem.models.test_case_def.get_test_case_definitions")
def test_parse_testcase(m_get_defs):
    m_get_defs.return_value = (
        '#tc000: ex=02 timing=1 size=0 panic=0 ranking=0 runtime=5 description="setup"'
    )
    tcs = get_all(disable_cache=True)
    assert 1 == len(tcs)
    assert 0 == tcs[0].id
    assert 2 == tcs[0].exercise_nr
    assert True == tcs[0].timing
    assert False == tcs[0].size
    assert False == tcs[0].panic
    assert False == tcs[0].ranking
    assert 5 == tcs[0].runtime
    assert "setup" == tcs[0].description


@mock.patch("testsystem.models.test_case_def.get_test_case_definitions")
def test_parse_invalid_testcase(m_get_defs):
    m_get_defs.return_value = (
        '#tc000: ex=02 t=1 s=0 p=0 r=0 runtime=5 description="setup"'
    )
    tcs = get_all(disable_cache=True)
    assert 0 == len(tcs)


@pytest.mark.parametrize("line", ["", "\n", " ", "   ", "   \n", ""])
@mock.patch("testsystem.models.test_case_def.get_test_case_definitions")
@mock.patch("testsystem.models.test_case_def.logging.warning")
def test_get_testcase_ignores_empty_line(m_warn, m_get_defs, line):
    m_get_defs.return_value = line
    tcs = get_all(disable_cache=True)
    assert 0 == len(tcs)
    m_warn.assert_not_called()


@mock.patch("testsystem.models.test_case_def.get_config")
@mock.patch("testsystem.models.test_case_def.get_all")
def test_get_testcases_for_active_or_previous_exercises(m_get_all, m_get_config):
    conf = Config()
    conf.exercise_nr = 1
    tcs = [
        TestCaseDef(exercise_nr=0),
        TestCaseDef(exercise_nr=1),
        TestCaseDef(exercise_nr=2),
    ]
    m_get_config.return_value = conf
    m_get_all.return_value = tcs
    result = get(disable_cache=True)
    assert 2 == len(result)
    assert tcs[0] == result[0]
    assert tcs[1] == result[1]


@mock.patch("testsystem.models.test_case_def.get_config")
@mock.patch("testsystem.models.test_case_def.get_all")
def test_do_not_include_timing_tests_if_disabled(m_get_all, m_get_config):
    conf = Config()
    conf.enable_timing_tests = False
    tcs = [TestCaseDef(timing=True), TestCaseDef(timing=False)]
    m_get_config.return_value = conf
    m_get_all.return_value = tcs
    result = get(disable_cache=True)
    assert 1 == len(result)
    assert tcs[1] == result[0]


@mock.patch("testsystem.models.test_case_def._tc_defs", None)
@mock.patch("testsystem.models.test_case_def._tc_defs_timestamp", 0)
@mock.patch("testsystem.models.test_case_def.time.time")
@mock.patch("testsystem.models.test_case_def.get_test_case_definitions")
def test_cache_timeout(m_get_tc_defs, m_time):
    base_time = 10000
    tc_def_raw = [
        '#tc001: ex=01 timing=0 size=0 panic=0 ranking=0 runtime=1 description="Test1"',
        '#tc002: ex=02 timing=0 size=0 panic=0 ranking=0 runtime=1 description="Test2"',
    ]
    m_get_tc_defs.return_value = tc_def_raw[0]
    m_time.return_value = base_time
    tc_defs1 = get_all()
    m_time.return_value = base_time + TC_DEF_CACHE_TIME_S - 1
    tc_defs2 = get_all()
    m_get_tc_defs.return_value = "\n".join(tc_def_raw)
    m_time.return_value = base_time + TC_DEF_CACHE_TIME_S
    tc_defs3 = get_all()
    assert len(tc_defs1) == 1
    assert len(tc_defs2) == 1
    assert len(tc_defs3) == 2


@mock.patch("testsystem.models.test_case_def._tc_defs", None)
@mock.patch("testsystem.models.test_case_def._tc_defs_timestamp", 0)
@mock.patch("testsystem.models.test_case_def.time.time")
@mock.patch("testsystem.models.test_case_def.get_test_case_definitions")
def test_renew_cache_after_timeout(m_get_tc_defs, m_time):
    base_time = 10000
    tc_def_raw = [
        '#tc001: ex=01 timing=0 size=0 panic=0 ranking=0 runtime=1 description="Test1"',
        '#tc002: ex=02 timing=0 size=0 panic=0 ranking=0 runtime=1 description="Test2"',
    ]
    m_get_tc_defs.return_value = tc_def_raw[0]
    m_time.return_value = base_time
    tc_defs1 = get_all()
    m_get_tc_defs.return_value = "\n".join(tc_def_raw)
    tc_defs2 = get_all()
    assert len(tc_defs1) == 1
    assert len(tc_defs2) == 1
