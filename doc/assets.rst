The assets Application
======================

The :py:mod:`assets` application provides a REST-full API for assets.


Installation
````````````

Add the assets application to your ``INSTALLED_APPS`` configuration as usual.
Make sure to configure the various ``ASSETS_OAUTH2_...`` settings.

Default settings
````````````````

.. automodule:: assets.defaultsettings
    :members:

Views and serializers
`````````````````````

.. automodule:: assets.views
    :members:

.. automodule:: assets.serializers
    :members:

Authentication and permissions
``````````````````````````````

.. automodule:: assets.oauth2client
    :members:

.. automodule:: assets.authentication
    :members:

.. automodule:: assets.permissions
    :members:

Extensions to drf-yasg
``````````````````````

.. automodule:: assets.inspectors
    :members:

Default URL routing
```````````````````

.. automodule:: assets.urls
    :members:


Application configuration
`````````````````````````

.. automodule:: assets.apps
    :members:
