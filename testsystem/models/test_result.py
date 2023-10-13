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

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship

import testsystem.db as db
from .test_case_def import TestCaseDef, is_score_tc


def get_score(test_result: TestResult) -> int:
    """
    Returns the value this test result contributes to the total score.
    """
    assert test_result.tc_def is not None
    if (
        is_score_tc(test_result.tc_def)
        and test_result.successful
        and test_result.result is not None
        and test_result.result >= 1
    ):
        return 1
    else:
        return 0


class TestResult(db.Base):
    """
    Class for a specific test result produced by a test case.
    This is also a database object.
    """

    __test__ = False

    __tablename__ = "TestResults"

    id: int = Column(Integer, primary_key=True)  # type: ignore
    test_set_id: int = Column(Integer, ForeignKey("TestSets.id"), nullable=False)  # type: ignore
    result: float | None = Column(Float, nullable=True)  # type: ignore
    test_case_id: int = Column(Integer, nullable=False)  # type: ignore
    successful: bool = Column(Boolean, nullable=False)  # type: ignore
    output: str = Column(String(4096), nullable=False, default="")  # type: ignore
    build_output: str | None = Column(String(4096), nullable=True)  # type: ignore
    build_error: str | None = Column(String(4096), nullable=True)  # type: ignore
    flash_output: str | None = Column(String(4096), nullable=True)  # type: ignore
    flash_error: str | None = Column(String(4096), nullable=True)  # type: ignore
    timestamp: int = Column(Integer, nullable=False)  # type: ignore

    test_set_result = relationship("TestSet", back_populates="test_results")

    @property
    def tc_def(self) -> TestCaseDef | None:
        """
        The test case definition for this result.
        This parameter would be none if the test case definition was deleted
        after the test result was created.
        """
        return TestCaseDef.get_by_id(self.test_case_id)

    @property
    def contribute_to_score(self) -> bool:
        """
        Returns true if this result should be considered in the result score.
        """
        tc_def = self.tc_def
        assert (
            tc_def is not None
        ), f"Missing test case definition for test case id {self.test_case_id}."
        return is_score_tc(tc_def)

    @property
    def score(self) -> int:
        """
        Returns the value this testcase contributes to the total score.
        """
        return get_score(self)
