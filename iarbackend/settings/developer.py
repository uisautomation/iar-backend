import os

# Import settings from the base settings file
from .base import *  # noqa: F401, F403

# Use Demo Raven server
UCAMWEBAUTH_LOGIN_URL = 'https://demo.raven.cam.ac.uk/auth/authenticate.html'
UCAMWEBAUTH_LOGOUT_URL = 'https://demo.raven.cam.ac.uk/auth/logout.html'
UCAMWEBAUTH_CERTS = {
    901: """
-----BEGIN CERTIFICATE-----
MIIDzTCCAzagAwIBAgIBADANBgkqhkiG9w0BAQQFADCBpjELMAkGA1UEBhMCR0Ix
EDAOBgNVBAgTB0VuZ2xhbmQxEjAQBgNVBAcTCUNhbWJyaWRnZTEgMB4GA1UEChMX
VW5pdmVyc2l0eSBvZiBDYW1icmlkZ2UxLTArBgNVBAsTJENvbXB1dGluZyBTZXJ2
aWNlIERFTU8gUmF2ZW4gU2VydmljZTEgMB4GA1UEAxMXUmF2ZW4gREVNTyBwdWJs
aWMga2V5IDEwHhcNMDUwNzI2MTMyMTIwWhcNMDUwODI1MTMyMTIwWjCBpjELMAkG
A1UEBhMCR0IxEDAOBgNVBAgTB0VuZ2xhbmQxEjAQBgNVBAcTCUNhbWJyaWRnZTEg
MB4GA1UEChMXVW5pdmVyc2l0eSBvZiBDYW1icmlkZ2UxLTArBgNVBAsTJENvbXB1
dGluZyBTZXJ2aWNlIERFTU8gUmF2ZW4gU2VydmljZTEgMB4GA1UEAxMXUmF2ZW4g
REVNTyBwdWJsaWMga2V5IDEwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBALhF
i9tIZvjYQQRfOzP3cy5ujR91ZntQnQehldByHlchHRmXwA1ot/e1WlHPgIjYkFRW
lSNcSDM5r7BkFu69zM66IHcF80NIopBp+3FYqi5uglEDlpzFrd+vYllzw7lBzUnp
CrwTxyO5JBaWnFMZrQkSdspXv89VQUO4V4QjXV7/AgMBAAGjggEHMIIBAzAdBgNV
HQ4EFgQUgjC6WtA4jFf54kxlidhFi8w+0HkwgdMGA1UdIwSByzCByIAUgjC6WtA4
jFf54kxlidhFi8w+0HmhgaykgakwgaYxCzAJBgNVBAYTAkdCMRAwDgYDVQQIEwdF
bmdsYW5kMRIwEAYDVQQHEwlDYW1icmlkZ2UxIDAeBgNVBAoTF1VuaXZlcnNpdHkg
b2YgQ2FtYnJpZGdlMS0wKwYDVQQLEyRDb21wdXRpbmcgU2VydmljZSBERU1PIFJh
dmVuIFNlcnZpY2UxIDAeBgNVBAMTF1JhdmVuIERFTU8gcHVibGljIGtleSAxggEA
MAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEEBQADgYEAsdyB+9szctHHIHE+S2Kg
LSxbGuFG9yfPFIqaSntlYMxKKB5ba/tIAMzyAOHxdEM5hi1DXRsOok3ElWjOw9oN
6Psvk/hLUN+YfC1saaUs3oh+OTfD7I4gRTbXPgsd6JgJQ0TQtuGygJdaht9cRBHW
wOq24EIbX5LquL9w+uvnfXw=
-----END CERTIFICATE-----
"""
}

DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + [  # noqa: F405
    'debug_toolbar',
]

MIDDLEWARE = MIDDLEWARE + [  # noqa: F405
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

STATIC_URL = '/static/'

if os.environ.get('IAR_USE_EXPERIMENTAL_OAUTH2_ENDPOINT') is not None:
    # These OAuth2 settings are correct only if the development server has been launched via
    # docker-compose.
    ASSETS_OAUTH2_TOKEN_URL = (
        'https://experimental-oauth2.gcloud.automation.uis.cam.ac.uk/oauth2/token')
    ASSETS_OAUTH2_INTROSPECT_URL = (
        'https://experimental-oauth2.gcloud.automation.uis.cam.ac.uk/oauth2/introspect')
    ASSETS_OAUTH2_CLIENT_ID = os.environ.get('IAR_CLIENT_ID')
    ASSETS_OAUTH2_CLIENT_SECRET = os.environ.get('IAR_CLIENT_SECRET')
    ASSETS_OAUTH2_INTROSPECT_SCOPES = ['hydra.introspect']

    # Set the OAuth2 authorisation endpoint
    SWAGGER_SETTINGS['SECURITY_DEFINITIONS']['oauth2']['authorizationUrl'] = (  # noqa: F405
        'https://experimental-oauth2.gcloud.automation.uis.cam.ac.uk/oauth2/auth')
else:
    # These OAuth2 settings are correct only if the development server has been launched via
    # docker-compose.
    ASSETS_OAUTH2_TOKEN_URL = 'http://hydra:4444/oauth2/token'
    ASSETS_OAUTH2_INTROSPECT_URL = 'http://hydra:4444/oauth2/introspect'
    ASSETS_OAUTH2_CLIENT_ID = 'hydraroot'
    ASSETS_OAUTH2_CLIENT_SECRET = 'secret'
    ASSETS_OAUTH2_INTROSPECT_SCOPES = ['hydra.introspect']

    # Set the OAuth2 authorisation endpoint
    SWAGGER_SETTINGS['SECURITY_DEFINITIONS']['oauth2']['authorizationUrl'] = (  # noqa: F405
    'http://localhost:4444/oauth2/auth')
