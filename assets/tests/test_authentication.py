"""
Test custom DRF authentication

"""
import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from requests import Response
from rest_framework.request import Request
from oauthlib.oauth2 import TokenExpiredError

from assets import authentication


class OAuth2Test(TestCase):
    GOOD_TOKEN = 'GOOD_TOKEN'
    UNKNOWN_TOKEN = 'UNKNOWN_TOKEN'
    FUTURE_TOKEN = 'FUTURE_TOKEN'
    PAST_TOKEN = 'PAST_TOKEN'
    NO_SUBJECT_TOKEN = 'NO_SUBJECT_TOKEN'

    def setUp(self):
        # Create an empty HTTP request
        self.request = Request(HttpRequest())
        self.auth = authentication.OAuth2TokenAuthentication()

    def test_no_token(self):
        """A request with no token is not authenticated."""
        self.assertIsNone(self.authenticate())

    def test_good_token(self):
        """A request with a good token is authenticated."""
        self.set_token(OAuth2Test.GOOD_TOKEN)
        with self.patch_oauth2_session():
            result = self.authenticate()
        self.assertIsNotNone(result)
        user, auth = result
        self.assertIsNotNone(user)
        self.assertIsInstance(auth, dict)

        # user should exist
        self.assertTrue(get_user_model().objects.filter(username='testing:test0001').exists())

    def test_empty_subject(self):
        """A request with a good token but no subject creates no user."""
        self.set_token(OAuth2Test.NO_SUBJECT_TOKEN)
        with self.patch_oauth2_session():
            result = self.authenticate()
        self.assertIsNotNone(result)
        user, auth = result
        self.assertIsNone(user)
        self.assertIsInstance(auth, dict)

    def test_unknown_token(self):
        """A request with an unknown token is not authenticated."""
        self.set_token(OAuth2Test.UNKNOWN_TOKEN)
        with self.patch_oauth2_session():
            result = self.authenticate()
        self.assertIsNone(result)

    def test_past_token(self):
        """A request with an past token is not authenticated."""
        self.set_token(OAuth2Test.PAST_TOKEN)
        with self.patch_oauth2_session():
            result = self.authenticate()
        self.assertIsNone(result)

    def test_future_token(self):
        """A request with an future token is not authenticated."""
        self.set_token(OAuth2Test.FUTURE_TOKEN)
        with self.patch_oauth2_session():
            result = self.authenticate()
        self.assertIsNone(result)

    def test_expired_token(self):
        """A request with an expired token results in the session being re-created."""
        self.set_token(OAuth2Test.GOOD_TOKEN)

        def mocked_request(*args, **kwargs):
            """Mocked request function for first call which raises TokenExpiredError."""
            raise TokenExpiredError

        # Mock the internal cached session so that mocked_request() is called and then, if all is
        # working, a new session is obtained via the session patched by patch_oauth2_session.
        cached_session_patch = mock.patch('assets.authentication._request.__session')

        with cached_session_patch as cached_session, self.patch_oauth2_session():
            cached_session.request.side_effect = mocked_request
            result = self.authenticate()
        self.assertIsNotNone(result)
        user, auth = result
        self.assertIsNotNone(user)
        self.assertIsInstance(auth, dict)

    def authenticate(self):
        """Convenience method to authenticate self.request against self.auth."""
        return self.auth.authenticate(self.request)

    def set_token(self, token):
        """Set the Bearer token for the request to *token*."""
        self.request.META['HTTP_AUTHORIZATION'] = 'Bearer ' + token

    def patch_oauth2_session(self):
        """Patch the internal request session used by the authenticator."""
        mock_request = mock.MagicMock()

        def side_effect(*args, **kwargs):
            token = kwargs.get('data', {}).get('token')

            # By default, the response is success with inactive token
            response = Response()
            response.status_code = 200
            response._content = json.dumps(dict(active=False)).encode('utf8')

            if token == OAuth2Test.GOOD_TOKEN:
                response._content = json.dumps(dict(
                    sub='testing:test0001',
                    active=True, iat=_utc_now() - 1000, exp=_utc_now() + 1000)).encode('utf8')
            elif token == OAuth2Test.FUTURE_TOKEN:
                response._content = json.dumps(dict(
                    sub='testing:test0001',
                    active=True, iat=_utc_now() + 1000, exp=_utc_now() + 3000)).encode('utf8')
            elif token == OAuth2Test.PAST_TOKEN:
                response._content = json.dumps(dict(
                    sub='testing:test0001',
                    active=True, iat=_utc_now() - 3000, exp=_utc_now() - 1000)).encode('utf8')
            elif token == OAuth2Test.NO_SUBJECT_TOKEN:
                response._content = json.dumps(dict(
                    active=True, iat=_utc_now() - 1000, exp=_utc_now() + 1000)).encode('utf8')
            elif token == OAuth2Test.UNKNOWN_TOKEN:
                pass  # default response suffices
            else:
                assert False, "Unexpected token value: {}".format(repr(token))

            return response

        mock_request.side_effect = side_effect

        # Mock OAuth2Session to return our session mock
        mock_get_session = mock.MagicMock()
        mock_get_session.return_value.request = mock_request

        return mock.patch('assets.authentication.OAuth2Session', mock_get_session)


def _utc_now():
    """Return a UNIX-style timestamp representing "now" in UTC."""
    return (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()
