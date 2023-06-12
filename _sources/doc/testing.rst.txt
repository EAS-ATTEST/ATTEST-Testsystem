=======================
Testing the test system
=======================

Test cases for the test system are categorized into unit and integration tests. The
latter comes with a sophisticated and tailored framework to add further test scenarios
easily. Further details on the test framework can be found in section :ref:`Integration
Test Framework`. Tests use the default python test framework in combination with pytest
for some additional features. They are located in the *tests* directory. 

Unit tests are only used for scenarios in which they are helpful. Decoding a UART signal
or scheduling tasks according to their priority are perfect examples of such cases.

To run the unit tests use the following command:

.. code-block::

  pytest tests/unit_tests

To generate an HTML unit test coverage report, you can run the VS Code Task ``Unit Test:
Coverage``. Once built, you can find the result in `htmlcov/index.html
<./../../../htmlcov/index.html>`_.

To run only the integration tests, use the pytest command as follows.

.. code-block::

  pytest tests/integration_tests

.. note::

  These tests require at least one MSP430 and a PicoScope, i.e., one test unit and will
  usually run for minutes.

Integration Test Framework
==========================

The test framework is primarily used for integration tests. Each integration test should
have its file (e.g: *tests/integration_tests/test_schedule_only_latest_commit.py*). The
file header should contain some information about the expected runtime of the test.
Additionally, each integration test should implement a main method to run and debug
tests individually. Another advantage of running an integration test as a standalone
python program is that you will see the logging output of the test system in the
terminal and the log file.


.. note::

    Pytest and the python unit test framework automatically consider each class or
    method starting with *Test* or *test* as a test case. If you still want to name a
    class or method *[tT]est* other than a test case, you can add the ``__test__ =
    False`` property. Each test case is then executed individually by the python test
    framework.

The integration tests use the following file system structure:

.. code-block::

    /                                       : Repository root directory.
    ├── __<test_name>                       : Temporal working directory for an integration test.
    |   ├── __git_remote                    : Contains the upstream repositories.
    |   ├── __git_local                     : Contains clones of the upstream repositories.
    |   ├── database.db                     : Database used for this integration test.
    |   └── config.json                     : Configuration file used for this integration test.
    └── tests/integration_tests             : Integration test directory
        ├── data                            : Contains data for integration tests
        |   ├── test_cases                  : Directory for committable data
        |   |   └── <tc_name>               : A specific test case (commit)
        |   |       ├── data                : Data that will be commited by a group. 
        |   |       |                       :   Usually an RTOS implementation.
        |   |       └── result.json         : Expected results from the test system.
        |   ├── RTOS_Public_SS00.tar.gz     : Archive of the initial public RTOS repository.
        |   ├── RTOS_SS00_GroupInit.tar.gz  : Archive of the initial group repository.
        |   └── Testsystem_Reports.tar.gz   : Archive of the initial system repository.
        ├── test_framework                  : Contains the test framework python package.
        └── <integration_test_name>.py      : A single integration test


.. note::

  Archiving the initial repositories is required to track them with git. Data in a test
  case should only be data and should not contain any git stuff, but the initial
  repositories must be a valid git clone with the required branches and an initial
  commit.

The parameter ``<test_name>`` in the directory structure is a friendly name for a
specific test case. The value for this parameter is set with the *name* argument in the
:py:attr:`~test_framework.test_system_model.TestSystemModel` constructor. The parameter
``<tc_name>`` is a specific test case used for integration tests, i.e., the data a group
will commit during an integration test run. The test case also contains the expected
results from the test system in a JSON file. For a detailed description of the result
file structure, look at the :py:class:`~test_framework.CommitAction` class. When adding
a commit action to a group, the *tc_name* value references this directory. The parameter
``<integration_test_name>`` is the name of the integration test. The filename should
start with *test_* so that it is recognized by pytest. Choosing the same value for
``<integration_test_name>`` and ``<test_name>`` is a viable option.


The temporal working directory will be deleted when the integration test finishes
successfully. To keep the directory for further inspection, set the *keep_repos*
argument in the :py:attr:`~test_framework.test_system_model.TestSystemModel`
constructor. To inspect a repository, use the *git remote* path to clone the result into
a new location. Do not change the state of the *git local* repositories. The test
framework uses these, and modifying them results in undefined behavior.


The test framework consists of three types of objects. The
:py:class:`~test_framework.test_system_model.TestSystemModel`,
:py:class:`~test_framework.group_model.GroupModel` and
:py:class:`~test_framework.action.Action`. In the scope of an integration test, only one
test system model should exist. A test system model can have up to 100 groups, which is
the current limit due to the group name format. And each group can have any number of
actions. 

Test System Model
-----------------

The :py:class:`~test_framework.test_system_model.TestSystemModel` is a wrapper for the
actual test system instance. It creates required repositories, sets up a test database,
handles configuration, and runs the test system. This wrapper only sets the context in
which the test system runs and does not modify the test system implementation in any
way. Isolating the test system in a test context is achieved using the environment
variables and config file described in section :ref:`Configuration`. This black box
approach means that integration tests use exactly the same test system implementation as
the production version.

New groups are added with the
:py:meth:`~test_framework.test_system_model.TestSystemModel.register_group` method from
the test system model. The communication between groups and the test system primarily
happens through git. An exception is the
:py:class:`~test_framework.stop_testsystem_action.StopTestsystemAction`, which uses the
test system configuration to shut down the instance.

Group Model
-----------

The :py:class:`~test_framework.group_model.GroupModel` simulates students' behavior
using a set of tasks they will work through. Group models, like students, make no
mistakes; if a group model is assessed with an incorrect result, the test system has
made a mistake.

Groups are not synchronized with each other and behave as parallel units. Actions in a
group, on the other hand, are strictly successive. This difference in synchronization
means that group 1 does not depend on any commit of group 2. Still, group 1 must first
commit, wait for the result and verify in this particular order. Though other orders
are possible, like committing twice before waiting, they will always be consecutive.

To add actions, the group has a generic
:py:meth:`~test_framework.group_model.GroupModel.add_action` method. But in most cases,
using one of the following convenience methods is sufficient: 

* :py:meth:`~test_framework.group_model.GroupModel.commit` Group commits a test case
  (``<tc_name>`` from above)
* :py:meth:`~test_framework.group_model.GroupModel.initial_commit` Commit that is
  already present when the system starts
* :py:meth:`~test_framework.group_model.GroupModel.stop_test_system` Shut down the test
  system; Integration test is completed
* :py:meth:`~test_framework.group_model.GroupModel.verify` Verify that the results from
  a report are correct
* :py:meth:`~test_framework.group_model.GroupModel.verify_any_report` Verify that no
  report was published until now
* :py:meth:`~test_framework.group_model.GroupModel.verify_no_report` Verify that no
  report for a specific commit was published
* :py:meth:`~test_framework.group_model.GroupModel.wait` Wait for some time
* :py:meth:`~test_framework.group_model.GroupModel.wait_report` Wait until a (specific)
  report is published

These methods can be chained together in an arbitrary order, which allows the
construction of complex group behaviors in a clean and simple way. Except for the
:py:meth:`~test_framework.group.Group.initial_commit`, these methods are setup methods.
Calling them registers an action but does not execute any logic. They will return
immediately. Actions are processed only upon starting the group, which is the case when
calling :py:meth:`~test_framework.test_system_model.TestSystemModel.run`. The run method
will only return when the test system is stopped. The following example shows the
definition of specific group behavior and its execution.

.. code-block:: python

    import test_framework as tf

    ts = tf.setup_test_system()
    group1 = ts.register_group(1)

    # Initialize group repo with test case 1
    tc1 = group1.initial_commit("tc1")
    # Commit test case 2
    tc2 = group1.commit("tc2")
    # Commit test case 3; wait for report from tc3 and verify it
    group1.commit("tc3").wait_report().verify()
    # Wait for report from test case 2
    rep2 = group1.wait_report(tc2)
    # Commit test case 4; verify report from tc2; wait for tc4 and verify it; 
    # verify that no report for tc1 is published
    group1.commit("tc4").verify(rep2).wait_report().verify().verify_no_report(tc1)
    # Test completed; shut down the test system
    group1.stop_test_system()
    
    ts.run()

.. warning::

    The previous example is an invalid test case for the current implementation of the
    test system. Its only purpose is to show the flexibility of the test framework. The
    test system only ever schedules the most recent commit. There will most likely be no
    report for tc1 and tc2, and therefore ``group1.wait_report(tc2)`` will never finish. 
    
     

Action
------

:py:class:`~test_framework.action.Action` is the base for every task performed by a group.
To add new behavior, derive from this class and implement ``def run(self)``. This method
should contain the logic and only return when the action is completed. The base class
has some handy properties, like a reference to its group, and already implements
exception handling. So it is safe to ``assert`` in the run method. The base class will
handle this, and the results will be printed when the test is finished. Optionally
extend the convenience methods in :py:class:`~test_framework.group_model.GroupModel` and
:py:class:`~test_framework.action.Action` to enable chaining of the new functionality.


Add new integration test
========================

The following template could be convenient when adding a new integration test. This
template starts a new test system instance and stops it right after finishing the
initialization procedure. It also implements the main method so that this test case can
be executed as a standalone program.

.. code-block:: python

    """
    Integration test template. This starts and stops the test system.

    +------------------+-------+-------+
    | Nr. Test Units   | 1     | 2     |
    +------------------+-------+-------+
    | Expected Runtime | ~0:00 | ~0:00 |
    +------------------+-------+-------+
    """

    import test_framework as tf

    def test_case():
        # Sets up a new instance of the test system
        ts = tf.setup_test_system("test_template")
        # Register a group on the test system
        group1 = ts.register_group(1)
        group1.stop_test_system()
        # Start the test system; will be stopped right after initialization.
        ts.run()

    if __name__ == "__main__":
        test_case()

Adding test cases (commitable data) to the test framework is similarly straightforward.
Create a subdirectory with an arbitrary name in the
*tests/integration_tests/data/test_cases directory*. In this directory, add a data
directory containing the data a group should commit and a *result.json* file with the
expected results. For more details on the structure, look at section :ref:`Integration
Test Framework` or at the :py:class:`~test_framework.commit_action.CommitAction` class
definition. To use the new data in an integration test use it as follows:

.. code-block:: python

    group.commit("arbitrary subdirectory name")
    group.wait_report().verify() # optional verification of results