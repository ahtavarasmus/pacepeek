from flask import Blueprint, redirect, url_for, session, request, flash
import requests
from pprint import pprint
from flask_login import login_user, current_user, logout_user
from sqlalchemy.exc import SQLAlchemyError
from .models import User
from . import db, config

github_auth = Blueprint('github_auth', __name__)

@github_auth.route('/login')
def login():
    return redirect(f'https://github.com/login/oauth/authorize?client_id={config.get("GITHUB_APP_CLIENT_ID")}')

@github_auth.route('/callback')
def callback():
    code = request.args.get('code')
    data = {'client_id': config.get('GITHUB_APP_CLIENT_ID'), 
            'client_secret': config.get('GITHUB_APP_CLIENT_SECRET'), 'code': code}
    headers = {'Accept': 'application/json'}
    response = requests.post('https://github.com/login/oauth/access_token', data=data, headers=headers)
    access_token = response.json()['access_token']

    # Save the access token in the session
    session['access_token'] = access_token

    user_data = requests.get('https://api.github.com/user', headers={'Authorization': f'token {access_token}'})
    github_id = user_data.json()['id']
    github_login = user_data.json()['login']
    github_name = user_data.json()['name']
    user = User.query.filter_by(github_id=github_id).first()
    if user is None:
        user = User(github_id=github_id, github_login=github_login, name=github_name)
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=True)
    flash(f'Welcome, {user.name}!', 'success')
    return redirect(url_for('views.home'))

@github_auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('views.home'))

