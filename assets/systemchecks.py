"""
The :py:mod:`assets` application ships with some custom system checks which ensure that the
``ASSETS_OAUTH2_...`` settings have non-default values. These system checks are registered by
the :py:class:`~assets.apps.AssetsConfig` class's
:py:meth:`~assets.apps.AssetsConfig.ready` method.

.. seealso::

    The `Django System Check Framework <https://docs.djangoproject.com/en/2.0/ref/checks/>`_.

"""
from django.conf import settings
from django.core.checks import register, Error


@register
def api_credentials_check(app_configs, **kwargs):
    """
    A system check ensuring that the OAuth2 credentials are specified.

    .. seealso:: https://docs.djangoproject.com/en/2.0/ref/checks/

    """
    errors = []

    # Check that all required settings are specified and non-None
    required_settings = [
        'ASSETS_OAUTH2_TOKEN_URL',
        'ASSETS_OAUTH2_INTROSPECT_URL',
        'ASSETS_OAUTH2_CLIENT_ID',
        'ASSETS_OAUTH2_CLIENT_SECRET',
        'ASSETS_OAUTH2_INTROSPECT_SCOPES',
        'LOOKUP_ROOT',
    ]
    for idx, name in enumerate(required_settings):
        value = getattr(settings, name, None)
        if value is None or value == '':
            errors.append(Error(
                'Required setting {} not set'.format(name),
                id='assets.E{:03d}'.format(idx + 1),
                hint='Add {} to settings.'.format(name)))

    return errors
