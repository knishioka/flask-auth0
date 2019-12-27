import os
import urllib.request
import urllib.parse

import flask
import flask_oauthlib.client
from jose import jwt


app = flask.Flask(__name__)
app.secret_key = 'this is secret'


AUTH0_CLIENT_ID = os.environ['AUTH0_CLIENT_ID']
AUTH0_CLIENT_SECRET = os.environ['AUTH0_CLIENT_SECRET']
AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN']


oauth = flask_oauthlib.client.OAuth(app)
auth0 = oauth.remote_app(
    'auth0',
    consumer_key=AUTH0_CLIENT_ID,
    consumer_secret=AUTH0_CLIENT_SECRET,
    request_token_params={
        'scope': 'openid profile',
        'audience': f'https://{AUTH0_DOMAIN}/userinfo',
    },
    base_url=f'https://{AUTH0_DOMAIN}',
    access_token_method='POST',
    access_token_url='/oauth/token',
    authorize_url='/authorize',
)


@app.route('/login')
def login():
    print(flask.url_for('auth_callback', _external=True))
    return auth0.authorize(callback=flask.url_for('auth_callback',
                                                  _external=True))


@app.route('/callback')
def auth_callback():
    resp = auth0.authorized_response()
    if resp is None:
        return 'nothing data', 403

    jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
    with urllib.request.urlopen(jwks_url) as jwks:
        key = jwks.read()

    try:
        payload = jwt.decode(resp['id_token'], key, audience=AUTH0_CLIENT_ID)
    except Exception as e:
        print(e)
        return 'something wrong', 403

    flask.session['profile'] = {
        'id': payload['sub'],
        'name': payload['name'],
        'picture': payload['picture'],
    }

    return flask.redirect(flask.url_for('mypage'))


@app.route('/mypage')
def mypage():
    if 'profile' not in flask.session:
        return flask.redirect(flask.url_for('login'))

    return '''
        <img src="{picture}"><br>
        name: <b>{name}</b><br>
        ID: <b>{id}</b><br>
        <br>
        <a href="/">back to top</a>
    '''.format(**flask.session['profile'])


@app.route('/logout')
def logout():
    del flask.session['profile']

    params = {'returnTo': flask.url_for('index', _external=True),
                  'client_id': AUTH0_CLIENT_ID}
    return flask.redirect(auth0.base_url +
                              '/v2/logout?'+
                              urllib.parse.urlencode(params))


@app.route('/')
def index():
    if 'profile' in flask.session:
        return '''
            welcome <a href="/mypage">{}</a>!<br>
            <br>
            <a href="/logout">logout</a>
        '''.format(flask.session['profile']['name'])
    else:
        return '''
            welcome!<br>
            <br>
            <a href="/login">login</a>
        '''.format(flask.url_for('login'))


if __name__ == '__main__':
    app.run()
