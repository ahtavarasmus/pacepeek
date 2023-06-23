from . import db,config

from .models import User, Repo
import openai
import requests
from flask import session
from flask_login import current_user
from requests_oauthlib import OAuth2Session

openai.api_key = config.get('OPENAI_API_KEY')


def get_repos():
    """
    Returns a dictionary of user's repositories and their owners from GitHub.

    Returns:
        repos_dict (dict): A dictionary of user's repositories and their owners from GitHub.
    """
    github = OAuth2Session(config.get('GITHUB_CLIENT_ID'), token=session['oauth_token'])
    repos_json = github.get('https://api.github.com/user/repos').json()
    repos_dict = {}
    for repo in repos_json:
        if not repo['private']:
            repo_name = repo['name']
            owner_login = repo['owner']['login']
            repos_dict[repo_name] = owner_login
    return repos_dict

def let_gpt_explain(changes: str):
    """
    Uses GPT-4 to explain the changes made in a commit.

    Args:
        changes (str): The changes made in a commit.

    Returns:
        message (str): The explanation of the changes made in a commit.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": """Welcome to the GPT-4 API. Your function is to analyze changes made in GitHub commits. When provided with a commit message and filenames their corresponding changes patches, your task is to summarize what changes the user, Rasmus, made. These summaries will be converted into clear, concise posts, ideally organized into bullet-point lists or similar formats. These posts are then uploaded to social media platforms, so they must be clear, easy-to-understand summaries of the changes. Even though the posts are written in third person and automated, they should still contain all relevant information in a manner that a person who didn't make those changes would understand.

Let's take a look at an example:

Based on a recent commit made by Rasmus, here's a breakdown of the key changes:

    Rasmus updated raw and contour plots, making them more interactive and user-friendly by using matplotlib.
    He added a line to the raw plot for better data visualization, which also interacts with the third plot.
    Moving the line on the raw plot now results in the corresponding adjustment of data on the third plot.
    He introduced new classes for RawPlot and ContourPlot, standardizing the plot generation process.
    Within these new classes, Rasmus included methods for data plotting and addition of draggable lines, simplifying the overall application use.
    The 'Invert & Plot' button has been re-labeled to 'Invert' for better clarity on its function.
    Rasmus removed some redundant code that was originally responsible for updating the plots, as the vertical lines now handle updates.

Remember, your output should be factual, concise, and clear, ensuring any reader can grasp the changes made.
"""},
            {"role": "user","content": f"{changes}"},
        ]
    )
    message = response["choices"][0]["message"]["content"]
    return message
