import os
from flask import Flask, jsonify, render_template, request, redirect, session, url_for
from markupsafe import escape
from oauthlib.oauth2 import OAuth2Error
from requests_oauthlib import OAuth2Session

app = Flask(__name__)

# Get this information by registering your app at https://developer.id.me
# Set IDME_BASE_URL=http://localhost:5001 to use the local mock (see mock_idme.py)
client_id              = os.environ.get('IDME_CLIENT_ID', 'YOUR_CLIENT_ID')
client_secret          = os.environ.get('IDME_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
redirect_uri           = os.environ.get('IDME_REDIRECT_URI', 'http://localhost:5000/callback')
base_url               = os.environ.get('IDME_BASE_URL', 'https://api.id.me').rstrip('/')
authorization_base_url = base_url + '/oauth/authorize'
token_url              = base_url + '/oauth/token'
attributes_url         = base_url + '/api/public/v3/attributes.json'
use_mock               = base_url != 'https://api.id.me'

# possible scope values: "military", "student", "responder", "government", "teacher"
scope = os.environ.get('IDME_SCOPE', 'military').split(',')

@app.route("/")

def demo():
    auth_url = None
    if use_mock:
        # The hosted ID.me button always points at api.id.me, so link directly when using the mock
        idme = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
        auth_url, session['oauth_state'] = idme.authorization_url(authorization_base_url)

    return render_template('index.html', client_id=client_id, redirect_uri=redirect_uri, scope=','.join(scope), auth_url=auth_url)

@app.route("/callback", methods=["GET"])
def callback():
    if request.args.get('error'):
        return "Authorization failed: %s" % escape(request.args['error']), 401

    # Exchange your code for an access token
    idme  = OAuth2Session(client_id, redirect_uri=redirect_uri, state=session.pop('oauth_state', None))
    try:
        token = idme.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
    except OAuth2Error as e:
        return "Authorization failed: %s" % escape(e.error), 401

    # At this point you can fetch a user's attributes but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    return redirect(url_for('.profile'))

@app.route("/profile", methods=["GET"])
def profile():
    if 'oauth_token' not in session:
        return redirect(url_for('.demo'))

    # Fetching the user's attributes using an OAuth 2 token.
    idme = OAuth2Session(client_id, token=session['oauth_token'])
    payload = idme.get(attributes_url).json()

    session['profile'] = 'true'
    return jsonify(payload)

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    app.secret_key = os.urandom(24)
    app.run(debug=True)
