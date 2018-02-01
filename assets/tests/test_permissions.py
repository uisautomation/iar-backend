"""
Test custom DRF permissions

"""
from django.http import HttpRequest
from django.test import TestCase
from rest_framework.request import Request

from assets import permissions


class HasScopesTest(TestCase):
    def setUp(self):
        # Create a mock incoming request and view
        self.request = Request(HttpRequest())
        self.view = HasScopesTest.MockView()
        self.perm = permissions.HasScopesPermission()

    def test_requires_auth(self):
        """Request must have authentication information."""
        self.assertFalse(self.has_permission())

    def test_requires_dict_auth(self):
        """Request authorisation must be a dictionary."""
        self.request.auth = 'foo'
        self.assertFalse(self.has_permission())

    def test_requires_scopes(self):
        """Token must have required scopes."""
        self.request.auth = {'scope': 'SCOPEA SCOPEB'}
        self.assertTrue(self.has_permission())
        self.request.auth = {'scope': 'SCOPEA'}
        self.assertFalse(self.has_permission())
        self.request.auth = {'scope': 'SCOPEB'}
        self.assertFalse(self.has_permission())

    def test_extra_scopes(self):
        """Token may have extra scopes."""
        self.request.auth = {'scope': 'SCOPEA SCOPEB SCOPEC'}
        self.assertTrue(self.has_permission())

    def has_permission(self):
        """
        Convenience method to return the has_permission() method value when evaluated on the
        test's request and view instances.

        """
        return self.perm.has_permission(self.request, self.view)

    class MockView:
        """A mock view class which defines two required scopes."""
        required_scopes = ['SCOPEA', 'SCOPEB']
