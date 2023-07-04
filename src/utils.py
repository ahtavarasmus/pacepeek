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

def let_gpt_explain(username: str, changes: str):
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
            {"role": "system", "content": f"""Welcome to the GPT-4 API. Your function is to analyze changes made in GitHub commits. When provided with a list of commit messages and filenames their corresponding changes patches, your task is to summarize what changes the user, {username}, made. Only when user has made some interesting choice of code should you explain the trick, but mostly you should not explain what the code does, you just explain what user did. For example if user implemented mostly just a known algorithm, you don't explain it, but just say that user used that algorithm. These summaries will be converted into clear, concise posts including bullet points of the changes. These posts are then uploaded to social media platforms, so they must be clear, easy-to-understand summaries of the changes. Even though the posts are written in third person and automated, they should still contain all relevant information in a manner that a person who didn't make those changes would understand.

Let's take a look at an example:

Based on recent commits made by {username}, here's a breakdown of the key changes:

    - {username} updated raw and contour plots, making them more interactive and user-friendly by using matplotlib.
    - He added a line to the raw plot for better data visualization, which also interacts with the third plot.
    - He introduced new classes for RawPlot and ContourPlot, standardizing the plot generation process.
    - Within these new classes, {username} included methods for data plotting and addition of draggable lines, simplifying the overall application use.
    - The 'Invert & Plot' button has been re-labeled to 'Invert' for better clarity on its function.
    - {username} removed some redundant code that was originally responsible for updating the plots, as the vertical lines now handle updates.

Remember, your output should be factual, concise, and clear, ensuring any reader can easily grasp the changes made.

             You should output the post as html, so that "-" indicates <li> item tag and paragraph <p> and so on.
"""},
            {"role": "user","content": f"{changes}"},
        ]
    )
    message = response["choices"][0]["message"]["content"]
    return message


def judge_significance(commit_patches_data: str) -> int:
    """
    Uses GPT-4 to judge the significance of a commit.

    Args:
        commit_patches_data (str): The commit patches data.

    Returns:
        score (int): The significance score of the commit.
    """
    prompt = f""""""
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": f"""Your task is to analyze the provided commits and their filenames and patches and evaluate their significance in terms of contributing to a summary post. If there is multiple commits you give the significance based on all of them and NOT judge them individually. Assign a significance score on a scale of 1 to 5 (integers, no floating point numbers), where 5 denotes 'significant enough for a summary post' and 1 denotes 'not enough significant changes'. 

For a commit/commits to score 5, it should contain at least one small, completed feature (approximately 100 lines of code), OR make significant progress on a larger feature compared to the features approx size, OR demonstrate substantial refactoring and code cleanup. 

Small refactors or deletions alone would not warrant a score of 5, unless they affect approximately 200 lines of code or more. 

If there is more than 5 commits to analyze, just give significance score 5.

Remember, you will not judge the commits individually, but rather as a whole.

Please analyze the following commit patches and assign a significance score:

{commit_patches_data}"""},
            {"role": "user","content": f"Please assign a significance score between 1 and 5 for the given commit patches."},
        ]
    )

    score = int(response['choices'][0]['message']['content'])
    return score


