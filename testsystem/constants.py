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

import os

from .pico_status_constants import PICO_ERROR_CODES

TESTSYSTEM_ROOT = os.environ.get("RTS_ROOT")
assert TESTSYSTEM_ROOT is not None, (
    "Define a path to the test system root directory. Use the RTS_ROOT environment"
    " variable to do that."
)

TESTSYSTEM_TITLE = r"""  _____ _______ ____   _____   _______        _                 _
 |  __ \__   __/ __ \ / ____| |__   __|      | |               | |
 | |__) | | | | |  | | (___      | | ___  ___| |_ ___ _   _ ___| |_ ___ _ __ ___
 |  _  /  | | | |  | |\___ \     | |/ _ \/ __| __/ __| | | / __| __/ _ \ '_ ` _ \
 | | \ \  | | | |__| |____) |    | |  __/\__ \ |_\__ \ |_| \__ \ ||  __/ | | | | |
 |_|  \_\ |_|  \____/|_____/     |_|\___||___/\__|___/\__, |___/\__\___|_| |_| |_|
                                                       __/ |
                                                      |___/                       """

MSP430_ELF_GCC = "msp430-elf-gcc"
MSP430_ELF_SIZE = "msp430-elf-size"
MSP430_FLASHER = "/bin/MSP430Flasher"
PICOMEASURE_BINARY = "picomeasure"
PICODETECT_BINARY = "picodetect"
LOG_INDENT = "   "
SCHEDULER_PAUSE_S = 10
GIT_RETRIES = 10
LEGACY_TASK_PRIO = 5
FORCE_TEST_TAG_PRIO = 25
MSP430_FLASHER_TIMEOUT_S = 20
DB_CONN_TIMEOUT_S = 20

CONFIG_CACHE_TIME_S = 10
GIT_PUBLIC_CACHE_TIME_S = 600

EE_BAD_COMMIT_MESSAGE_ENABLED = True
EE_BAD_COMMIT_MESSAGE_TEXT = "Definitely you."
EE_BAD_COMMIT_MESSAGE_URL = "https://imgs.xkcd.com/comics/git_commit.png"
EE_BAD_COMMIT_MESSAGES = [
    "small changes",
    "small change",
    "change",
    "update",
    ".",
    "..",
    "...",
]

COM_PORT_MSP_VID = 8263  # Vendor ID
COM_PORT_MSP_PID = 19  # Product ID
COM_PORT_MSP_DEBUG_IDENTIFIER = "MSP Debug Interface"
COM_PORT_MSP_UART_IDENTIFIER = "MSP Application UART"

MSP_ID_IDENTIFIER_PATH = os.path.join(TESTSYSTEM_ROOT, "testsystem/msp430-identifier")
MSP_ID_DEVICE_ID_TEMPLATE = "<DEVICE_ID>"
MSP_ID_GENERATOR_DEFINE = "__RTS_GEN"
MSP_ID_SAMPLES_PER_BIT = 3
MSP_ID_BAUD_RATE = 1200
MSP_ID_START_PATTERN = 0xFE

TEST_ID_LENGTH = 3
TEST_OUTPUT_DIR_NAME = "output"
TEST_TESTBENCHE_DIR_NAME = "testbenches"
TEST_DEFINITION_FILE = "testcases.txt"
TEST_BEGIN_MARKER = "TESTCASE BEGIN\n"
TEST_NEVER_IN_OUTPUT = "[NOT PANICED!]\n"
TEST_HEADER_FILES = [
    "testsystem.h",
    "queueCheck.h",
]
TEST_GROUP_SRC_FILES = ["*.c", "*.h", "*.s", "*.S"]
TEST_ENVIRONMENT_DIRECTORY = "/testenv/"
TEST_MSP430_UART_BAUDRATE = 9600
TEST_TIMING_CLK_DEVIDER = 32
TEST_TIMING_RUNS = 1
TEST_MAX_TIMING_RETRIES = 2
TEST_ACCEPTABLE_TIMING_VARIANCE_US = 2  # Variance of TIMING_RUNS must be less than this
TEST_RETRIES = 3

GIT_PUBLIC_NAME_TEMPLATE = "RTOS_Public_{0}"
GIT_LOCAL_ROOT_DIR = "/git/"
GIT_RESULT_BRANCH_NAME = "testresults"

REPORT_DISABLE_BUILD_OUTPUT = True
REPORT_DISABLE_FLASH_OUTPUT = True

DEBUG_COLLECT_FAILED_BUILD_ARTEFACTS = False
DEBUG_FAILED_BUILD_ARTEFACTS_DIR = "/host/build_artefacts"

TUTAG_SCOPE = "scope"

PICO_CLOCK_SAMPLING_NS = 500  # ns
PICO_LOGIC_THRESHOLD_VOLTAGE = 1.7
