from . import db,config

from .models import User, Repo
import requests
from flask import session
from flask_login import current_user
from requests_oauthlib import OAuth2Session



def get_repos():
    """
    Returns a dictionary of user's repositories and their owners from GitHub.
    """
    github = OAuth2Session(config.get('GITHUB_CLIENT_ID'), token=session['oauth_token'])
    repos_json = github.get('https://api.github.com/user/repos').json()
    repos_dict = {}
    for repo in repos_json:
            
        repo_name = repo['name']
        owner_login = repo['owner']['login']
        repos_dict[repo_name] = owner_login
    return repos_dict

def get_watch_list():
    """
    Returns a list of repositories that the user is watching.
    """
    watch_list = []
    return watch_list

def setup_webhook(user: User, repo_name: str, owner_login: str):
    url = f"https://api.github.com/repos/{owner_login}/{repo_name}/hooks"
    headers = {
        'Authorization': f"token {user.github_token}",
        'Accept': 'application/vnd.github.v3+json',
    }
    payload = {
        'name': 'web',
        'active': True,
        'events': ['push'],
        'config': {
            'url': 'https://your-app.com/payload',  # Replace with your server's URL.
            'content_type': 'json',
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        print(f"Failed to set up webhook for {repo_name}: {response.content}")
        return False
    return True
