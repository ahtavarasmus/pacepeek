from flask import session
from pprint import pprint
from . import config,db
from .models import User, Post, Commit, Patch
from .utils import judge_significance, generate_summary
import requests



def setup_webhook(user: User, repo_name: str, owner_login: str):
    """
    Sets up a webhook for the repository.
    """
    
    data = {
        'name': 'web',
        'active': True,
        'events': ['push'],
        'config': {
            'url': f'{config.get("APP_URL")}/webhook', 
            'content_type': 'json',
        }
    }
    access_token = session.get('access_token')
    headers = {'Authorization': f'token {access_token}'}
    response = requests.post(f'https://api.github.com/repos/{owner_login}/{repo_name}/hooks', json=data, headers=headers)
    print("response",response)
    if response.status_code != 201:
        print(f"Failed to set up webhook for {repo_name}: {response.content}")
        return None

    return response.json()['id']


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

def get_commit_patches_data(owner_login: str, repo_name: str, commit_sha: str) -> str:
    """
    Retrieves the patch for a commit.

    Args:
        owner_login (str): The owner of the repository.
        repo_name (str): The name of the repository.
        commit_sha (str): The SHA of the commit.
    Returns:
        str: The patches for the commit in a nice format.
    """

    post = Post.query.filter_by(repo=repo_name, not_finished=True).first()
    if not post:
        user = User.query.filter_by(login=owner_login).first()
        post = Post(user=user,repo=repo_name)
        db.session.add(post)

    # find the new commits data
    github = get_github_session(owner_login)
    new_commit_json = github.get(f'https://api.github.com/repos/{owner_login}/{repo_name}/commits/{commit_sha}').json()

    # add the new commit to the database
    commit_message = new_commit_json['commit']['message']
    url = f"https://github.com/{owner_login}/{repo_name}/commit/{commit_sha}"
    new_commit = Commit(message=commit_message, post=post, sha=commit_sha, link=url)
    db.session.add(new_commit)

    # add the new commit patches to the database
    for file in new_commit_json['files']:
        # Check if 'patch' exists in the file dictionary
        if 'patch' in file:
            new_patch = Patch(filename=file['filename'], commit=new_commit)
            patch = file['patch']
            new_patch.patch_body = patch
            db.session.add(new_patch)

    db.session.commit()

    # make the commits and patches data into a nice format
    data = ""
    for commit in post.commits:
        changes = {'message': commit.message}
        data += f"Commit Message: {commit.message} \n"
        data += "Files: \n"
        for patch in commit.patches:
            data += f"  File: {patch.filename} \n"
            data += f"  Patch: {patch.patch_body} \n"

    return data

def handle_payload(payload: dict):
    """
    Handles a webhook payload from GitHub.
    """
    commit_sha = payload['after']
    repo_name = payload['repository']['name']
    owner_login = payload['repository']['owner']['login']
    commit_patches_data = get_commit_patches_data(owner_login, repo_name, commit_sha)
    sig = judge_significance(commit_patches_data)
    if sig is None:
        print('Error judging significance')
        return
    print(sig.lower())
    if sig.lower() == "significant":
        post_text = generate_summary(commit_patches_data)
        if post_text is None:
            print('Error generating summary')
            return
        post = Post.query.filter_by(repo=repo_name, not_finished=True).first()
        post.not_finished = False
        post.text = post_text
        db.session.commit()
        print(post)
    else:
        print("Not significant")



