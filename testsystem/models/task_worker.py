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
import logging
import threading
import testsystem.scheduling as scheduling
from testsystem.constants import TU_UNAVAILABLE_RETRY_INTERVAL_S
from .test_unit import TestUnit


class TaskWorker:
    """
    Worker class for a test unit. This class executes task on a test unit.

    :param test_unit: The test unit which should be used by this worker.
    :param name: A name for this worker.
        This is only for easier log inspection and has no functional purpose.
    """

    def __init__(self, test_unit: TestUnit, name: str):
        self.test_unit = test_unit
        self.running = False
        self.thread: threading.Thread | None = None
        self.idle = True
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def start(self):
        """
        Start the task worker.
        """
        assert self.thread is None
        logging.info(
            f"[{self.name}] Starting... ({self.test_unit.msp430},"
            f" {self.test_unit.picoscope})"
        )
        self.running = True
        self.thread = threading.Thread(target=self.__run)
        self.thread.start()

    def stop(self):
        """
        Stop the task worker. This call can block for a while because the test unit
        might need some time to stop its current task.
        """
        assert self.thread is not None
        logging.info(
            f"[{self.name}] Stopping... ({self.test_unit.msp430},"
            f" {self.test_unit.picoscope})"
        )
        self.running = False
        self.thread.join()

    def __run(self):
        logging.info(f"[{self.name}] Started successful.")
        while self.running:
            if not self.test_unit.is_available():
                logging.warning(
                    f"[{self.name}] Test unit ({self.test_unit.msp430},"
                    f" {self.test_unit.picoscope}) currently unavailable."
                )
                time.sleep(TU_UNAVAILABLE_RETRY_INTERVAL_S)
                continue

            task = scheduling.get_next_task(self)
            if task is None:
                self.idle = True
                time.sleep(1)
            else:
                self.idle = False
                logging.debug(f"[{self.name}] Start {task}.")
                task.run_safe(self.test_unit)
                logging.debug(f"[{self.name}] Finished {task}.")
        logging.info(f"[{self.name}] Stopped successful.")
