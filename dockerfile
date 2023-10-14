FROM ubuntu:20.04

# Required for GDB
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends tzdata git

# Build and install boost 1.67; requirement for libmsp430
WORKDIR /software
RUN apt-get update && apt-get install -y wget build-essential gcc g++ libc6-dev make
RUN wget https://boostorg.jfrog.io/artifactory/main/release/1.67.0/source/boost_1_67_0.tar.gz
RUN tar -xf boost_1_67_0.tar.gz
WORKDIR /software/boost_1_67_0
RUN ./bootstrap.sh
RUN ./b2 cxxflags=-fPIC cflags=-fPIC install --with-filesystem --with-system --with-date_time --with-chrono --with-thread --prefix=/usr

# Build and install hidapi library; requirement for libmsp430
WORKDIR /software
RUN apt-get update && apt-get install -y pkg-config libudev-dev libusb-1.0-0-dev autotools-dev autoconf automake libtool
RUN git clone -b hidapi-0.8.0-rc1 https://github.com/signal11/hidapi.git
WORKDIR /software/hidapi
RUN ./bootstrap
RUN ./configure --prefix=/usr
RUN make
RUN make install

# Build libmsp430
WORKDIR /software/libmsp430/
RUN apt-get update && apt-get install -y wget p7zip-full
RUN wget https://dr-download.ti.com/software-development/driver-or-library/MD-4vnqcP1Wk4/3.15.1.1/MSPDebugStack_OS_Package_3_15_1_1.zip
RUN 7z x MSPDebugStack_OS_Package_3_15_1_1.zip
RUN ln -s /usr/include/hidapi/hidapi.h /software/libmsp430/ThirdParty/include/hidapi.h
RUN mkdir -p /software/libmsp430/ThirdParty/lib64/
RUN ln -s /usr/lib/libhidapi-libusb.so /software/libmsp430/ThirdParty/lib64/hid-libusb.o
RUN make
RUN cp /software/libmsp430/libmsp430.so /usr/lib/libmsp430.so
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/lib"

# Build and install msp-flasher
WORKDIR /software/msp-flasher-1_03_20/
RUN wget https://dr-download.ti.com/software-development/software-programming-tool/MD-szn5bCveqt/1.03.20.00/MSPFlasher-1_03_20_00-linux-x64-installer.zip
RUN 7z x MSPFlasher-1_03_20_00-linux-x64-installer.zip
RUN chmod +x MSPFlasher-1.3.20-linux-x64-installer.run
RUN ./MSPFlasher-1.3.20-linux-x64-installer.run --mode unattended
RUN cp /root/ti/MSPFlasher_1.3.20/MSP430Flasher /bin/MSP430Flasher

# Install picotech
WORKDIR /software/picotech/
RUN wget -qO - https://labs.picotech.com/Release.gpg.key | apt-key add -
RUN bash -c 'echo "deb https://labs.picotech.com/picoscope7/debian/ picoscope main" >/etc/apt/sources.list.d/picoscope7.list'
RUN mkdir -p /etc/udev/rules.d/
RUN apt-get update && apt-get download libps2000a
RUN mv -f libps2000a*.deb libps2000a.deb
RUN mkdir tmp
RUN dpkg-deb -R libps2000a.deb tmp
RUN sed -i '/udevadm control/d' tmp/DEBIAN/postinst
RUN dpkg-deb -b tmp libps2000a.deb
RUN apt-get install -y ./libps2000a.deb
ENV C_INCLUDE_PATH="${C_INCLUDE_PATH}:/opt/picoscope/include"
ENV LIBRARY_PATH="${LIBRARY_PATH}:/opt/picoscope/lib"

# Install msp430-gcc
WORKDIR /software/msp430-gcc
RUN wget https://dr-download.ti.com/software-development/ide-configuration-compiler-or-debugger/MD-LlCjWuAbzH/9.3.1.2/msp430-gcc-full-linux-x64-installer-9.3.1.2.7z
RUN 7z x msp430-gcc-full-linux-x64-installer-9.3.1.2.7z
RUN ./msp430-gcc-full-linux-x64-installer-9.3.1.2.run --mode unattended
ENV PATH="${PATH}:/root/ti/msp430-gcc/bin"
ENV C_INCLUDE_PATH="${C_INCLUDE_PATH}:/root/ti/msp430-gcc/include"
ENV LINKER_SCRIPT_PATH="/root/ti/msp430-gcc/include"

RUN apt-get update && apt-get install -y python3 pip

# Install picosdk python wrappers
WORKDIR /software
RUN git clone https://github.com/picotech/picosdk-python-wrappers.git
WORKDIR /software/picosdk-python-wrappers
RUN git checkout 2daf8e68edc29b54eb0e17e64f4d1d7492e7c260
RUN python3 setup.py install

# Install packages
RUN apt-get update && apt-get install -y srecord usbutils sqlite ssh

# Add host directory
WORKDIR /host

# Add testcases
WORKDIR /testcases
COPY testcases/ .

# Add testsystem
WORKDIR /testsystem
COPY requirements.txt ./

# Install python packages
RUN pip install -r requirements.txt

COPY *.py ./
COPY index.rst ./
COPY Makefile ./
COPY doc/ ./doc/
COPY tests/ ./tests/
COPY testsystem/ ./testsystem/

RUN git config --global user.email "attest@testsystem.com"
RUN git config --global user.name "ATTEST-Testsystem"

ENV PYTHONPATH=/testsystem:/testsystem/tests/integration_tests
ENV OS=unix
ENV INCLUDES=/root/ti/msp430-gcc/include/
ENV FLASHTOOL_MSP430=MSP430Flasher
ENV ATTEST_ROOT=/testsystem
ENV LC_ALL=C