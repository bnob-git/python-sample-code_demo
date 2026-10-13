# Local stand-in for the ID.me OAuth 2.0 endpoints used by server.py, for demos without ID.me credentials.
# Run: python mock_idme.py (port 5001), then: IDME_BASE_URL=http://localhost:5001 python server.py
import os
import re
import secrets
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from flask import Flask, jsonify, redirect, render_template_string, request

app = Flask(__name__)

SUBGROUPS = {
    'military':  'Veteran',
    'student':   'Student',
    'responder': 'EMT',
    'teacher':   'Teacher',
}

CODES  = {}
TOKENS = {}

SIGN_IN_PAGE = """
<html>
  <head><title>ID.me (mock) - Sign in</title></head>
  <body style="font-family: sans-serif; max-width: 420px; margin: 40px auto;">
    <h2>ID.me (mock)</h2>
    <p><strong>{{ client_id }}</strong> is requesting your <strong>{{ scope }}</strong> verification status.</p>
    <form method="post" action="/oauth/authorize">
      <input type="hidden" name="client_id" value="{{ client_id }}">
      <input type="hidden" name="redirect_uri" value="{{ redirect_uri }}">
      <input type="hidden" name="scope" value="{{ scope }}">
      <input type="hidden" name="state" value="{{ state }}">
      <p><label>First name <input name="fname" value="Jane"></label></p>
      <p><label>Last name <input name="lname" value="Doe"></label></p>
      <p><label>Email <input name="email" value="jane.doe@example.com"></label></p>
      <button type="submit" name="decision" value="allow">Allow</button>
      <button type="submit" name="decision" value="deny">Deny</button>
    </form>
  </body>
</html>
"""


def redirect_with(redirect_uri, query):
    parts = urlsplit(redirect_uri)
    params = parse_qsl(parts.query) + [(k, v) for k, v in query.items() if v]
    return redirect(urlunsplit(parts._replace(query=urlencode(params))))


def oauth_error(status, error, description):
    return jsonify(error=error, error_description=description), status


@app.route('/oauth/authorize', methods=['GET'])
def authorize_page():
    args = request.args
    if not args.get('client_id') or not args.get('redirect_uri'):
        return 'Missing client_id or redirect_uri', 400
    if args.get('response_type') != 'code':
        return 'Unsupported response_type', 400

    return render_template_string(SIGN_IN_PAGE, client_id=args['client_id'], redirect_uri=args['redirect_uri'],
                                  scope=args.get('scope', ''), state=args.get('state', ''))


@app.route('/oauth/authorize', methods=['POST'])
def authorize_decision():
    form = request.form
    if form.get('decision') != 'allow':
        return redirect_with(form['redirect_uri'], {'error': 'access_denied', 'state': form.get('state')})

    code = secrets.token_hex(16)
    CODES[code] = {
        'client_id':    form['client_id'],
        'redirect_uri': form['redirect_uri'],
        'scope':        form.get('scope', ''),
        'user':         {'uuid': secrets.token_hex(16), 'fname': form.get('fname'),
                         'lname': form.get('lname'), 'email': form.get('email')},
    }
    return redirect_with(form['redirect_uri'], {'code': code, 'state': form.get('state')})


@app.route('/oauth/token', methods=['POST'])
def token():
    form = request.form
    client_id = request.authorization.username if request.authorization else form.get('client_id')

    if form.get('grant_type') != 'authorization_code':
        return oauth_error(400, 'unsupported_grant_type', 'Only authorization_code is supported')

    grant = CODES.pop(form.get('code', ''), None)
    if not grant:
        return oauth_error(400, 'invalid_grant', 'Unknown or already used code')
    if grant['client_id'] != client_id:
        return oauth_error(401, 'invalid_client', 'client_id does not match the code')
    if grant['redirect_uri'] != form.get('redirect_uri'):
        return oauth_error(400, 'invalid_grant', 'redirect_uri does not match')

    access_token = secrets.token_hex(24)
    TOKENS[access_token] = grant
    return jsonify(access_token=access_token, token_type='bearer', expires_in=300,
                   refresh_token=secrets.token_hex(24), scope=grant['scope'])


@app.route('/api/public/v3/attributes.json', methods=['GET'])
def attributes():
    match = re.match(r'Bearer (.+)', request.headers.get('Authorization', ''), re.IGNORECASE)
    grant = TOKENS.get(match.group(1) if match else request.args.get('access_token', ''))
    if not grant:
        return oauth_error(401, 'invalid_token', 'Missing or invalid access token')

    user = grant['user']
    return jsonify(
        attributes=[
            {'handle': 'fname', 'name': 'First Name', 'value': user['fname']},
            {'handle': 'lname', 'name': 'Last Name', 'value': user['lname']},
            {'handle': 'email', 'name': 'Email', 'value': user['email']},
            {'handle': 'uuid', 'name': 'Unique Identifier', 'value': user['uuid']},
        ],
        status=[{'group': group, 'subgroups': [SUBGROUPS.get(group, group.capitalize())], 'verified': True}
                for group in re.split(r'[ ,]', grant['scope']) if group],
    )


if __name__ == '__main__':
    app.run(port=int(os.environ.get('MOCK_IDME_PORT', 5001)))
