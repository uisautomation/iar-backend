"""
OAuth2 authentication for Django REST Framework views.

"""
import datetime
import logging
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authentication import BaseAuthentication
import requests.exceptions
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError


LOG = logging.getLogger()


def _get_session():
    """
    Get a :py:class:`requests.Session` object which is authenticated with the API application's
    OAuth2 client credentials.

    """
    client = BackendApplicationClient(client_id=settings.ASSETS_OAUTH2_CLIENT_ID)
    session = OAuth2Session(client=client)
    session.fetch_token(
        timeout=2, token_url=settings.ASSETS_OAUTH2_TOKEN_URL,
        client_id=settings.ASSETS_OAUTH2_CLIENT_ID,
        client_secret=settings.ASSETS_OAUTH2_CLIENT_SECRET,
        scope=settings.ASSETS_OAUTH2_INTROSPECT_SCOPES)
    return session


def _request(*args, **kwargs):
    """
    A version of :py:func:`requests.request` which is authenticated with the OAuth2 token for the
    API server's client credentials. If the token has timed out, it is requested again.

    """
    if getattr(_request, '__session', None) is None:
        _request.__session = _get_session()
    try:
        return _request.__session.request(*args, **kwargs)
    except TokenExpiredError:
        _request.__session = _get_session()
        return _request.__session.request(*args, **kwargs)


def _utc_now():
    """Return a UNIX-style timestamp representing "now" in UTC."""
    return (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()


class OAuth2TokenAuthentication(BaseAuthentication):
    """
    Django REST framework authentication which accepts an OAuth2 token as a Bearer token and
    verifies it via the token introspection endpoint. If verification fails, the token is ignored.

    Sets request.auth to the parsed JSON response from the token introspection endpoint.

    Sets request.user to a Django user whose username matches the token's "sub" field (if set).

    **TODO:** Perform some token verification caching.

    """
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '').split(' ')
        if len(auth) != 2 or auth[0] != self.keyword:
            return None

        bearer = auth[1]

        token = self.validate_token(bearer)
        if token is None:
            return None

        # get or create a matching Django user if the token has a subject field, otherwise return
        # no user.
        subject = token.get('sub', '')

        if subject != '':
            # Our subjects are of the form '<scheme>:<identifier>'. Form a valid Django username
            # from these values.
            scheme, identifier = subject.split(':')
            username = '{}+{}'.format(scheme, identifier)

            # This is not quite the same as the default get_or_create() behaviour because we make
            # use of the create_user() helper here. This ensures the user is created and that
            # set_unusable_password() is also called on it.
            try:
                user = get_user_model().objects.get(username=username)
            except ObjectDoesNotExist:
                user = get_user_model().objects.create_user(username=username)

            if cache.get("{user.username}:lookup".format(user=user)) is None:
                # Adding 10 extra seconds to the expiry so that if the API requests takes long
                # the cache doesn't get expired between the authentication and the response
                lookup_response = requests.get(
                    settings.LOOKUP_SELF + "?fetch=all_insts,all_groups",
                    headers={"Authorization": "Bearer %s" % bearer})

                try:
                    # Ensure the response succeeded
                    lookup_response.raise_for_status()

                    # Cache the response body as parsed JSON
                    cache.set("{user.username}:lookup".format(user=user), lookup_response.json(),
                              datetime.timedelta(token['exp'] - _utc_now()).seconds+10)
                except requests.exceptions.HTTPError as error:
                    LOG.error(
                        ('HTTP Error {error} retrieving institutions for user "{user.username}" '
                         'with subject {subject}').format(error=error, user=user, subject=subject))
                    LOG.error('Payload was: {}'.format(lookup_response.content))
        else:
            user = None

        return (user, token)

    def validate_token(self, token):
        """
        Helper method which validates a Bearer token and returns the parsed response from the
        introspection endpoint if the token is valid. If the token is invalid, None is returned.

        A valid token must be active, be issued in the past and expire in the future.

        """
        r = _request(method='POST', url=settings.ASSETS_OAUTH2_INTROSPECT_URL,
                     timeout=2, data={'token': token})
        r.raise_for_status()
        token = r.json()
        if not token.get('active', False):
            return None

        # Get "now" in UTC
        now = _utc_now()

        if token['iat'] > now:
            LOG.warning('Rejecting token with "iat" in the future: %s with now = %s"',
                        (token['iat'], now))
            return None

        if token['exp'] < now:
            LOG.warning('Rejecting token with "exp" in the past: %s with now = %s"',
                        (token['exp'], now))
            return None

        # HACK: lookup:anonymous is required for the moment since we make use of the token/self
        # lookupproxy endpoint *and* we do so using the bearer token provided to the backend by the
        # user. TODO: refactor this to use the lookupproxy as the backend client.
        if 'lookup:anonymous' not in token.get('scope', '').split(' '):
            LOG.warning(
                'Presented bearer token with no lookup:anonymous scope. Permissions checking '
                'will be broken.')

        return token

    def authenticate_header(self, request):
        """
        Return a string used to populate the WWW-Authenticate header for a HTTP 401 response.

        """
        return 'Bearer'
