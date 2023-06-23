from requests_oauthlib import OAuth2Session
from pprint import pprint
from . import config
from .models import User
from .utils import let_gpt_explain
import requests



def setup_webhook(user: User, repo_name: str, owner_login: str):
    """
    Sets up a webhook for the given repository.
    """
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
            'url': 'https://2671e04ad2ab.ngrok.app/payload',  # Replace with your server's URL.
            'content_type': 'json',
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        print(f"Failed to set up webhook for {repo_name}: {response.content}")
        return False
    return True


def get_github_session(user_login):
    """
    Creates an OAuth2Session for a user.

    Args:
        user_login (str): The login of the user.

    Returns:
        OAuth2Session: The authenticated GitHub session for the user.
    """
    access_token = User.query.filter_by(login=user_login).first().github_token
    token = {
        'access_token': access_token,
        'token_type': 'Bearer'  # GitHub uses the Bearer token type
    }
    github = OAuth2Session(config.get('GITHUB_CLIENT_ID'), token=token)
    return github

def get_commit_patches(owner_login: str, repo_name: str, commit_sha: str):
    """
    Retrieves the patch for a commit.

    Args:
        owner_login (str): The owner of the repository.
        repo_name (str): The name of the repository.
        commit_sha (str): The SHA of the commit.
    Returns:
        changes (dict): {message: str, file_patches: dict}
    """
    github = get_github_session(owner_login)
    specific_commit_json = github.get(f'https://api.github.com/repos/{owner_login}/{repo_name}/commits/{commit_sha}').json()
    changes = {}
    commit_message = specific_commit_json['commit']['message']
    changes['message'] = commit_message
    file_patches = {}
    for file in specific_commit_json['files']:
        # Check if 'patch' exists in the file dictionary
        filename = file['filename']
        if 'patch' in file:
            patch = file['patch']
            file_patches[filename] = patch
    changes['file_patches'] = file_patches
    return changes

def handle_payload(payload):
    """
    Handles a webhook payload from GitHub.
    """
    commit_sha = payload['after']
    repo_name = payload['repository']['name']
    owner_login = payload['repository']['owner']['login']
    commit_patches = get_commit_patches(owner_login, repo_name, commit_sha)
    # making these patches into a nicer format to prompt to gpt
    changes = f"Message: {commit_patches['message']} \n"
    changes += "Files: \n"
    for filename, patch in commit_patches['file_patches'].items():
        changes += f"File: {filename} \n"
        changes += f"Patch: {patch} \n"
    post = let_gpt_explain(changes)
    print(post)


