from . import db,config

from .models import User, Repo
import openai
import requests
from flask import session
from flask_login import current_user
from requests_oauthlib import OAuth2Session
from datetime import datetime

openai.api_key = config.get('OPENAI_API_KEY')


def get_next_posts():

    oldest_post_time = session.get("oldest_post_time",default=datetime.utcnow())
    all_legal_posts = []
    for user in current_user.followers:
        user_posts = Post.query.filter((Post.user_id == user.id) & (Post.time_stamp > oldest_post_time)).all()

        all_legal_posts.append(user_posts)

    next_posts = []
    next_posts = sorted(next_posts, key=lambda x: x.time_stamp, reverse=True)[:5]

    if next_posts:
        session['oldest_post'] = next_posts[-1].time_stamp.timestamp()
    return next_posts



def get_repos(github_login: str):
    """
    Returns a dictionary of user's repositories and their owners from GitHub.

    Returns:
        repos_dict (dict): A dictionary of user's repositories and their owners from GitHub.
    """
    try:
        response = requests.get(f'https://api.github.com/users/{github_login}/repos')
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    
    repos = response.json()
    return [repo['name'] for repo in repos]


def generate_summary(commit_patches_data: str) -> str:
    """
    Uses GPT-4 to generate a summary of a commit.

    Args:
        commit_patches_data (str): The commit patches data.

    Returns:
        summary (str): The summary of the commit.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": f"""Your task is to summarize the following commit patches into a concise, easily readable message that describes the functional changes made. Do not just state what files were changed or added, but explain the changes in terms of their functionality and impact. For instance, if an algorithm was implemented, describe which algorithm it is and what problem it solves. The summary should be brief, like a Tweet (max 280 characters). 

    Here are the commit patches:

    {commit_patches_data}"""},
                {"role": "user","content": f"Please generate a brief summary of these commit patches, focusing on the functionality of the changes."},
            ]
        )

        if 'choices' in response and 'message' in response['choices'][0] and 'content' in response['choices'][0]['message']:
            summary = response['choices'][0]['message']['content']
        else:
            raise ValueError('Unexpected response format')
            
    except Exception as e:
        print(f'Error: {str(e)}')
        summary = None

    return summary



def judge_significance(commit_patches_data: str):
    """
    Uses GPT-4 to judge the significance of a commit.

    Args:
        commit_patches_data (str): The commit patches data.

    Returns:
        significance (str): 'significant' or 'not significant'
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": f"""Your task is to analyze the provided commits and evaluate their significance. If there are multiple commits, analyze them collectively. Your response should indicate whether these commits are 'significant' or 'not significant'.

    A 'significant' commit could:
    - Add a new feature or substantially progress a larger feature
    - Perform a major refactor or significant code cleanup

    A 'not significant' commit could:
    - Involve minor tweaks or bug fixes
    - Add comments or documentation
    - Perform small refactoring tasks

    Please judge the following commit patches and determine their significance by outputing only 'significant' or 'not significant'.:

    {commit_patches_data}"""},
                {"role": "user","content": f"Please evaluate if the given commit patches are 'significant' or 'not significant'."},
            ]
        )

        if 'choices' in response and 'message' in response['choices'][0] and 'content' in response['choices'][0]['message']:
            significance = response['choices'][0]['message']['content']
        else:
            raise ValueError('Unexpected response format')
            
    except Exception as e:
        print(f'Error: {str(e)}')
        significance = None

    return significance

