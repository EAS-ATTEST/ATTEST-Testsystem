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

import argparse
import testsystem as ts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="RTOS Testsystem",
        description=(
            "Testsystem for Real-Time Operating Systems course on TU Graz Institute of"
            " Technical Informatics."
        ),
    )
    parser.add_argument(
        "--set-name",
        nargs=2,
        metavar=("SN", "Name"),
        help="Set the name for a device by its serial number.",
    )
    parser.add_argument(
        "--hello-testsystem",
        action="store_true",
        help=(
            "The test system runs its hello world equivalent, displaying some general"
            " information."
        ),
    )
    parser.add_argument(
        "-ls",
        "--list-devices",
        action="store_true",
        help="List devices known by the test system.",
    )
    parser.add_argument(
        "--run-startup",
        action="store_true",
        help=(
            "Execute only the starup routine. The test system exits before entering the"
            " working mode."
        ),
    )
    parser.add_argument(
        "--run-idle",
        action="store_true",
        help=(
            "Start the test system in idle mode. The test system won't do anything in"
            " this mode. This is useful to start the container from the bootstrap"
            " script and investigate its state."
        ),
    )

    args = parser.parse_args()

    if args.set_name is not None:
        sn, name = args.set_name
        ts.set_device_name(sn, name)
    elif args.hello_testsystem:
        ts.run_hello_testsystem()
    elif args.list_devices:
        ts.list_devices()
    elif args.run_startup:
        ts.startup_routine()
    elif args.run_idle:
        ts.idle()
    else:
        ts.run()
