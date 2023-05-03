# ATTEST: Automated and Thorough Testing of Embedded Software in Teaching
RTOS Testsystem is a python-based test system for the Real-Time Operating Systems course in the [Embedded Automotive Systems](https://iti.tugraz.at/eas) group at the [Institute of Technical Informatics](https://www.tugraz.at/en/institutes/iti/home) at [Graz University of Technology](https://www.tugraz.at/home). It was
revised from scratch in the winter term of 2022 to improve its performance and
functionality. The system utilizes dedicated external hardware for testing to guarantee precise and reliable results. It is firmly git-oriented to embed its functionality in the best possible way.

## Getting started

The test system is easiest to use with the provided docker file. The current implementation uses MSP430 microcontroller boards as _target devices_ and 2205A PicoScopes as _measurement devices_. These devices form _test units_. A test unit is the dedicated hardware where test cases are executed.

### Requirements and Installation

Install docker by following the official [setup instructions](https://docs.docker.com/engine/install/ubuntu/).

The test system is supposed to run as a docker container, but there are still some
requirements on the host system. Run the following command to install the required
packages.

```
apt-get update && apt-get install -y git usbutils
```


### Start the Testsystem
If you just want to start the test system run the following command:

```
./bootstrap.sh
```

Or run the hello world equivalent:
```
./bootstrap.sh --hello-testsystem
```

If you already have an MSP430 or a PicoScope connected to your host, you can check the availability by running the startup routine.
```
./bootstrap.sh --run-startup
```

### Docker
The test system runs in a docker container. We suggest you first build the docker image because this may take a while.

```
docker build -t rts:latest .
```

When you have the docker image ready, you can inspect the available commands of the test system.

```
docker run --rm -t rts:latest python3 main.py --help
```

## Documentation
For comprehensive documentation, please visit the [project website](https://eas-attest.github.io/ATTEST-Testsystem/index.html).

Or you build the documentation locally by running the following command after you have the docker image ready. The documentation will be generated in the current working directory.

```
docker run --rm -t \
    -v "$(pwd)":/host rts:latest \
    bash -c "make html && cp -R _build/html /host/documentation"
```

## Contributing
The recommended way for developing the test system is by using VSCode and the
development container feature. The project contains a dev container configuration for
VSCode to make contributions as easy as possible. To start the dev container, press
``CTRL``+``SHIFT``+``P``, type ``Dev Containers: Open Folder in Container...`` and
select the cloned test system directory. The dev container configures the environment,
includes all the required packages, and contains some useful VS Code extensions for
development. If test units are available, add the respective devices to the ``runArgs``
section in the ``.devcontainer/devcontainer.json`` file and restart the container by typing ``Dev
Containers: Rebuild Container`` into the VSCode Command Palette. 


## Authors
* [Meinhard Kissich](mailto:meinhard.kissich@tugraz.at)
* [Klaus Weinbauer](mailto:klaus.weinbauer@student.tugraz.at)
* [Marcel Baunach](mailto:baunach@tugraz.at)

## Cite

**TODO**

## License
This project is published under the [MIT license](./LICENSE.txt).
