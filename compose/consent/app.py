import logging
import os

from flask import Flask, request, render_template, redirect
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient


LOG = logging.getLogger()
logging.basicConfig(level=logging.INFO)

CLIENT_ID, CLIENT_SECRET = os.environ['FORCE_ROOT_CLIENT_CREDENTIALS'].split(':')
SCOPES = ['hydra.consent']

TOKEN_ENDPOINT = 'http://hydra:4444/oauth2/token'
CONSENT_ENDPOINT = 'http://hydra:4444/oauth2/consent/requests/'

app = Flask(__name__)


@app.route('/')
def index():
    return 'This is the consent app'


@app.route('/consent', methods=['GET'])
def consent_get():
    session = get_session()

    error = request.args.get('error')
    error_description = request.args.get('error_description')
    if error is not None:
        return render_template('error.html', error=error, error_description=error_description)

    consent_id = request.args.get('consent')
    if consent_id is None:
        return render_template(
            'error.html',
            error='no consent id',
            error_description='No consent ID was given for the request')

    r = session.get(CONSENT_ENDPOINT + consent_id)
    r.raise_for_status()
    consent = r.json()

    return render_template('consent.html', consent=consent)


@app.route('/consent', methods=['POST'])
def consent_post():
    session = get_session()

    consent_id = request.args.get('consent')
    if consent_id is None:
        return 'no consent id'

    r = session.get(CONSENT_ENDPOINT + consent_id)
    r.raise_for_status()
    consent = r.json()

    username = request.form['username']

    session.patch(
        CONSENT_ENDPOINT + consent_id + '/accept', json={
            'grantScopes': consent['requestedScopes'],
            'subject': 'example:' + username,
        })

    return redirect(consent['redirectUrl'])


def get_session():
    LOG.info('Fetching initial token')
    client = BackendApplicationClient(client_id=CLIENT_ID)
    session = OAuth2Session(client=client)
    access_token = session.fetch_token(
        timeout=1, token_url=TOKEN_ENDPOINT,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scope=SCOPES,
        verify=False)
    LOG.info('Got access token: %r', access_token)

    return session
