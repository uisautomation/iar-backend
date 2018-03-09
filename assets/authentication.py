"""
OAuth2 authentication for Django REST Framework views.

"""
import datetime
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authentication import BaseAuthentication

from .models import UserLookup
from .oauth2client import AuthenticatedSession


LOG = logging.getLogger()

#: An authenticated session which introspect tokens
INTROSPECT_SESSION = AuthenticatedSession(scopes=settings.ASSETS_OAUTH2_INTROSPECT_SCOPES)


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
            user = user_from_subject(subject)
        else:
            user = None

        return user, token

    @staticmethod
    def validate_token(token):
        """
        Helper method which validates a Bearer token and returns the parsed response from the
        introspection endpoint if the token is valid. If the token is invalid, None is returned.

        A valid token must be active, be issued in the past and expire in the future.

        """
        r = INTROSPECT_SESSION.request(method='POST', url=settings.ASSETS_OAUTH2_INTROSPECT_URL,
                                       timeout=2, data={'token': token})
        r.raise_for_status()
        token = r.json()
        if not token.get('active', False):
            return None

        # Get "now" in UTC
        now = _utc_now()

        if token['iat'] > now:
            LOG.warning('Rejecting token with "iat" in the future: %s with now = %s"',
                        token['iat'], now)
            return None

        if token['exp'] < now:
            LOG.warning('Rejecting token with "exp" in the past: %s with now = %s"',
                        token['exp'], now)
            return None

        return token

    def authenticate_header(self, request):
        """
        Return a string used to populate the WWW-Authenticate header for a HTTP 401 response.

        """
        return 'Bearer'


def user_from_subject(subject):
    """
    Return a Django user object given a token subject.

    """
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

    # Record this association of user, subject and lookup identity in the DB. Since the user is
    # marked as the primary key field, this will throw a database error if there is an existing
    # record with differing scheme and identifier.
    UserLookup.objects.get_or_create(user=user, scheme=scheme, identifier=identifier)

    return user
