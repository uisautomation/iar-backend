"""
Test that the registered system checks work as expected.

"""
from django.core.management import call_command
# Q: is this a documented import location for SystemCheckError?
from django.core.management.base import SystemCheckError
from django.test import TestCase


class RequiredSettings(TestCase):
    """
    Required settings are set.

    """
    required_settings = [
        'OAUTH2_TOKEN_URL',
        'OAUTH2_INTROSPECT_URL',
        'OAUTH2_CLIENT_ID',
        'OAUTH2_CLIENT_SECRET',
        'OAUTH2_INTROSPECT_SCOPES',
        'LOOKUP_ROOT'
    ]

    @staticmethod
    def test_checks_pass():
        """The system checks should succeed in the test suite configuration."""
        call_command('check')

    def test_checks_fail(self):
        """The system check should fail if any required setting is unset or blank."""
        for name in self.required_settings:
            with self.settings(**{name: ''}), self.assertRaises(SystemCheckError):
                call_command('check')
            with self.settings(**{name: None}), self.assertRaises(SystemCheckError):
                call_command('check')
