from requests_oauthlib import OAuth2Session
from pprint import pprint
from . import config
from .models import User


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
    pprint(commit_patches)

