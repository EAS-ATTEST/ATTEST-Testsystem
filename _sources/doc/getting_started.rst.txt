===============
Getting Started
===============

This section provides a brief overview of the installation and essential configuration
tasks.

Installation
============

The test system is supposed to run as a docker container, but there are still some
requirements on the host system. Run the following command to install the required
packages.

.. code-block::

    sudo apt-get update && \
        sudo apt-get install -y git usbutils

Install docker by following the official `setup instructions
<https://docs.docker.com/engine/install/ubuntu/>`_.

If you still need to do so, clone the test system repository. The repository contains a
bootstrap script :ref:`Bootstrap Script` to start the test system container. This script
builds the container and maps available USB devices to the container. Once the container
is built, the test system starts and waits for commits.

Changing Semester
=================

For a new semester, the configuration must be adjusted accordingly. The following
properties should be set (in config file or environment variables):

* :py:attr:`~testsystem.config.Config.exercise_nr` = 1
* :py:attr:`~testsystem.config.Config.term` = "SSxx" where xx represent the year
* :py:attr:`~testsystem.config.Config.git_student_path` = "eas/teaching/RTOS_SSxx"
* :py:attr:`~testsystem.config.Config.git_public_path` = "eas/teaching/RTOS_SSxx"
* :py:attr:`~testsystem.config.Config.git_system_path` = "eas/teaching/RTOS_SSxx/Testsystem_Reports_SSxx"
* :py:attr:`~testsystem.config.Config.group_ids` = [1, 2, 3, 4, ...] 

Assuming the new group, public, and system repositories are already created, the
following command should run without errors:

.. code-block::

    ./bootstrap.sh --run-startup
