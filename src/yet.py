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

