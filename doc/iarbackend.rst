The iar-backend Project
=======================

The ``iarbackend`` project contains top-level configuration and URL routes for
the entire web application.

Settings
--------

The ``iarbackend`` project ships a number of settings files.

.. _settings:

Generic settings
````````````````

.. automodule:: iarbackend.settings
    :members:

.. _settings_testsuite:

Test-suite specific settings
````````````````````````````

.. automodule:: iarbackend.settings.tox
    :members:

.. _settings_developer:

Developer specific settings
```````````````````````````

.. automodule:: iarbackend.settings.developer
    :members:

Custom test suite runner
------------------------

The :any:`test suite settings <settings_testsuite>` overrides the
``TEST_RUNNER`` setting to point to
:py:class:`~iarbackend.tests.runner.BufferedTextTestRunner`. This runner captures
output to stdout and stderr and only reports the output if a test fails. This
helps make our tests a little less noisy.

.. autoclass:: iarbackend.tests.runner.BufferedDiscoverRunner

.. autoclass:: iarbackend.tests.runner.BufferedTextTestRunner
