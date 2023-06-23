from flask import Blueprint, redirect, url_for, session, request, flash
from flask_login import login_user, current_user, logout_user
from requests_oauthlib import OAuth2Session
from .models import User
from . import db,config

github_auth = Blueprint('github_auth', __name__)

@github_auth.route('/login')
def login():
    github = OAuth2Session(config.get('GITHUB_CLIENT_ID'),redirect_uri=config.get('GITHUB_REDIRECT_URI'),scope=config.get('GITHUB_SCOPE'))
    authorization_url, state = github.authorization_url(config.get('GITHUB_AUTHORIZATION_URL'))
    session['oauth_state'] = state
    print(f"Stored state {state}")
    return redirect(authorization_url)

@github_auth.route('/github-callback')
def github_callback():
    github = OAuth2Session(config.get('GITHUB_CLIENT_ID'),state=session['oauth_state'])
    print(f"Retrieved state {session['oauth_state']}")

    token = github.fetch_token(config.get('GITHUB_TOKEN_URL'), 
                                   client_secret=config.get('GITHUB_CLIENT_SECRET'), 
                                   authorization_response=request.url)
    session['oauth_token'] = token

    github_user_data = github.get('https://api.github.com/user').json()
    github_user_email = github_user_data.get('email')
    user = User.query.filter_by(email=github_user_email).first()
    if not user:
        user = User(username=github_user_data['name'],login=github_user_data['login'],email=github_user_email,github_token=token['access_token'])
        db.session.add(user)
        db.session.commit()
    else:
        user.github_token = token['access_token']
        db.session.commit()
    login_user(user, remember=True)
    flash('Logged in!', category='success')
    return redirect(url_for('views.home'))


@github_auth.route('/logout')
def logout():
    logout_user()

    session.clear()
    return redirect(url_for('views.home'))
