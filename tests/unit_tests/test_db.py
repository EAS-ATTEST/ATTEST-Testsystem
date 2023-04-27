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
import testsystem.db as db
import pytest
import unittest.mock as mock


@mock.patch("testsystem.db.get_config")
def test_init_db_with_unsupported_type(m_get_config):
    c = cnf.Config()
    c.db_type = "unsupported"
    m_get_config.return_value = c

    with pytest.raises(NotImplementedError) as e_info:
        db.init_database()


@mock.patch("testsystem.db.get_config")
def test_get_engine_inits_db(m_get_config):
    c = cnf.Config()
    c.db_file = "unit_test.db"
    m_get_config.return_value = c
    assert db.get_engine() is not None


@mock.patch("testsystem.db.get_config")
def test_init_db_twice(m_get_config):
    c = cnf.Config()
    c.db_file = "unit_test.db"
    m_get_config.return_value = c
    engine1 = db.get_engine()
    engine2 = db.get_engine()
    assert engine1 == engine2
