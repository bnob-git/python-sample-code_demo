# ID.me Sample Python Web App
This is a sample seed Python Web App integrated with ID.me via OAuth 2.0

# Installation and Setup
In order to run the example you need to have `python` and `pip` installed.

First set your client configuration settings with environment variables (read by `server.py`)

````bash
export IDME_CLIENT_ID='YOUR_CLIENT_ID'
export IDME_CLIENT_SECRET='YOUR_CLIENT_SECRET'
export IDME_REDIRECT_URI='http://localhost:5000/callback'

# possible scope values: "military", "student", "responder", "government", "teacher" (comma-separated)
export IDME_SCOPE='military'
````

Run the following to install the dependencies and start the server.

````bash
pip install -r requirements.txt
python server.py
````

Now you can view the app at [http://localhost:5000](http://localhost:5000)

# Running without ID.me credentials
`mock_idme.py` is a local stand-in for the ID.me authorize, token and attributes endpoints, so the full
OAuth flow (sign in, `/callback`, `/profile`) can be demoed without an ID.me developer account.

````bash
python mock_idme.py                                    # mock ID.me on http://localhost:5001
IDME_BASE_URL=http://localhost:5001 python server.py   # app on http://localhost:5000
````

The mock accepts any client id/secret, issues single-use codes and returns sample attributes for the requested scope.
