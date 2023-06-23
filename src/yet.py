"""
github = OAuth2Session(config.get('GITHUB_CLIENT_ID'), token=session['oauth_token'])
    repos_json = github.get('https://api.github.com/user/repos').json()
    html_msg = f"<h1>Logged in as {current_user.username}</h1><p>Your repos are:</p><ul>"
    for i,repo in enumerate(repos_json):
        if i >= 1:
            break;
            
        repo_name = repo['name']
        print("NAME:",repo_name)
        owner_login = repo['owner']['login']
        commits_json = github.get(f'https://api.github.com/repos/{owner_login}/{repo_name}/commits').json()
        html_msg += f"<li><h2>Repo: {repo_name}, Owner: {owner_login}</h2>"
        # check if the repository has any commits
        if isinstance(commits_json, list):
            html_msg += "<ul>"
            for commit in commits_json:
                commit_sha = commit['sha']
                specific_commit_json = github.get(f'https://api.github.com/repos/{owner_login}/{repo_name}/commits/{commit_sha}').json()
                commit_message = commit['commit']['message']
                html_msg += f"<li>Details for {commit_message}:</li><ul>"
                for file in specific_commit_json['files']:
                    # Check if 'patch' exists in the file dictionary
                    filename = file['filename']
                    if 'patch' in file:
                        patch = file['patch']
                        html_msg += f"<li>File: {filename}, Changes: {patch}</li>"
                html_msg += "</ul>"
            html_msg += "</ul>"
        else:
            html_msg += "<p>This repository has no commits.</p>"
        html_msg += "</li>"
    html_msg += "</ul>"

    return html_msg

"""
# SYSTEM MESSAGE FOR GPT
"""
Welcome to the GPT-4 API. Your function is to analyze changes made in GitHub commits. When provided with a commit message and a change patch, your task is to summarize what changes the user, Rasmus, made. These summaries will be converted into clear, concise posts, ideally organized into bullet-point lists or similar formats. These posts are then uploaded to social media platforms, so they must be clear, easy-to-understand summaries of the changes. Even though the posts are written in third person and automated, they should still contain all relevant information in a manner that a person who didn't make those changes would understand.

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
"""
