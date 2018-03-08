"""
Default settings values for the :py:mod:`assets` application.

"""
# Variables whose names are in upper case and do not start with an underscore from this module are
# used as default settings for the assets application. See AssetsConfig in .apps for
# how this is achieved. This is a bit mucky but, at the moment, Django does not have a standard way
# to specify default values for settings.  See: https://stackoverflow.com/questions/8428556/

ASSETS_OAUTH2_CLIENT_ID = None
"""
OAuth2 client id which the API server uses to identify itself to the OAuth2 token introspection
endpoint.

"""

ASSETS_OAUTH2_CLIENT_SECRET = None
"""
OAuth2 client secret which the API server uses to identify itself to the OAuth2 token introspection
endpoint.

"""

ASSETS_OAUTH2_TOKEN_URL = None
"""
URL of the OAuth2 token endpoint the API server uses to request an authorisation token to perform
OAuth2 token introspection.

"""

ASSETS_OAUTH2_INTROSPECT_URL = None
"""
URL of the OAuth2 token introspection endpoint. The API server will first identify itself to the
OAuth2 token endpoint and request an access token for this endpoint.

"""

ASSETS_OAUTH2_INTROSPECT_SCOPES = None
"""
List of OAuth2 scopes the API server will request for the token it will use with the token
introspection endpoint.

"""

LOOKUP_SELF = None
"""
URL of the LookupProxy endpoint that the authentication uses to get data about the user logged in.

"""

IAR_USERS_LOOKUP_GROUP = None
"""
Name of lookup group which a user must be a member of to have access to IAR.

"""
