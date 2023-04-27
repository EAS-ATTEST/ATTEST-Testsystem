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

from subprocess import Popen, PIPE
import sys
import testsystem.constants as const


def testMSP430GCCInstallation():
    try:
        process = Popen([const.MSP430_ELF_GCC], stderr=PIPE, stdout=PIPE)
        process.communicate(timeout=1)
    except:
        print(
            "[ERROR] msp430-elf-gcc is missing. "
            "Something went wrong during msp430-gcc installation."
        )
        sys.exit(1)

    try:
        process = Popen([const.MSP430_ELF_SIZE], stderr=PIPE, stdout=PIPE)
        process.communicate(timeout=1)
    except:
        print(
            "[ERROR] msp430-elf-size is missing. "
            "Something went wrong during msp430-gcc installation."
        )
        sys.exit(1)

    print("[INFO] msp430-gcc installed successful.")


def testPicomeasureInstallation():
    try:
        measure_process = Popen([const.PICOMEASURE_BINARY], stderr=PIPE, stdout=PIPE)
        measure_process.communicate(timeout=1)
    except:
        print("[ERROR] picomeasure is missing. Please compile the picomeasure binary.")
        print(
            "        gcc picomeasure.c -I/opt/picoscope/include -L/opt/picoscope/lib/ -lps2000a -o picomeasure -O3"
        )
        sys.exit(2)

    print("[INFO] picomeasure installed successful.")


def testPicodetectInstallation():
    try:
        detect_process = Popen([const.PICODETECT_BINARY], stderr=PIPE, stdout=PIPE)
        output, err = detect_process.communicate(timeout=5)
    except:
        print("[ERROR] picodetect is missing. Please compile the picodetect binary!")
        print(
            "        gcc picodetect.c -I/opt/picoscope/include -L/opt/picoscope/lib/ -lps2000a -o picodetect -O3"
        )
        sys.exit(3)

    print("[INFO] picodetect installed successful.")


def installationTest():
    testMSP430GCCInstallation()
    testPicomeasureInstallation()
    testPicodetectInstallation()


if __name__ == "__main__":
    installationTest()
