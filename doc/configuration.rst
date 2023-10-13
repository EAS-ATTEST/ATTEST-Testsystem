=============
Configuration
=============

The test system supports multiple ways of configuration and comes with default values as
a solid starting point for a functioning system. Environment variables and a JSON config
file are available to customize the test system.

.. note::

    JSON config has the highest priority, followed by environment variables. A property
    set in the config file overrides an environment variable if present and the default
    values.

Noteworthy properties
=====================

Some of the most essential parameters for operational use are the following:

* :py:attr:`~testsystem.config.Config.exercise_nr` The exercise number up to which
  testing is done.
* :py:attr:`~testsystem.config.Config.group_ids` A list of group ids participating in
  the course.
* :py:attr:`~testsystem.config.Config.term` The current term.
* :py:attr:`~testsystem.config.Config.tu_connections` Defines which connections must
  exist between a MSP430 and a PicoScope to form a Test Unit.

For a comprehensive list of available settings, look at the
:py:class:`~testsystem.config.Config` class.

Environment Variables
=====================

Configuration via environment variables can be used to customize the test system on
startup. Environment variables are instrumental when the system runs as a docker image
or as part of docker-compose. The naming convention for environment variables is
UPPER_CASE with underscores and prefixed with ``ATTEST_`` \.

.. note::

    To set a list parameter with an environment variable, concatenate the values with 
    ``;``.

To change the parameter :py:attr:`~testsystem.config.Config.run_hello_testsystem`, which
starts the hello world equivalent for the test system, you would set the following
environment variable:

.. code-block::

    ATTEST_RUN_HELLO_TESTSYSTEM=True


Config File
=====================

The config file enables dynamic configuration changes without restarting the test
system. Keep in mind that some settings won't take effect when set for a running
instance, for example, the database type is only used during startup. But in general,
assigning a value in the JSON config will take effect the next time the test system
requests the parameter. The file has a flat hierarchy with coherent camelCase or
PascalCase property names.

The JSON config to change the parameter
:py:attr:`~testsystem.config.Config.run_hello_testsystem` would look like one of the
following examples:
    
.. code-block:: javascript

    {
        "runHelloTestsystem": true
    }

.. code-block:: javascript

    {
        "RunHelloTestsystem": true
    }

Notice that changing this setting after startup will not affect the system because
:py:attr:`~testsystem.config.Config.run_hello_testsystem` is only used during startup.

.. note::

    The default config file path is ``./config.json`` relative to the test system root 
    directory. To change the path take a look at the 
    :py:attr:`~testsystem.config.Config.conf_file` property.

Default Configuration
=====================

The default configuration serves as a starting point to spin up a functioning instance
of the test system. These parameters are set in :py:class:`~testsystem.config.Config`
and should usually not be changed. Changes in default parameters would be subject to
source code and implementation changes. The default values should guarantee that the
current implementation runs without further configuration.

How to use and extend Config
============================

If you need an additional configuration parameter for further extension of the test
system, add a member to the :py:class:`~testsystem.config.Config` class with a short
description of its functionality as a comment. To access the configuration in code use
the :py:func:`~testsystem.config.get_config` function as followed:

.. code-block:: python

    from testsystem.config import get_config

    config = get_config()