from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

from flask_login import login_required, current_user
from requests_oauthlib import OAuth2Session

from src.github_auth import login
from . import db,config
from .models import User, Repo
from pprint import pprint
from .utils import get_repos, setup_webhook


views = Blueprint('views', __name__)


@login_required
@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html", user=current_user)

@login_required
@views.route('/profile')
def profile():
    repos = Repo.query.filter_by(user_id=current_user.id).all()
    return render_template("profile.html", user=current_user, repos=repos)

@login_required
@views.route('/get-repos',methods=['GET'])
def get_repos_route():
    repos = get_repos()
    repo_options = "\n".join(f'<option value="{name}:{login}">{name}</option>' for name,login in repos.items())
    form_html = f'''
    <form action="/add-repo-to-watch-list" method="post">
        <select id="repos" name="repos">
            <option value="">Select a repo...</option>
            {repo_options}
        </select>
        <input type="submit" value="Add to Watch List">
    </form>
    '''
    return form_html

@login_required
@views.route('/add-repo-to-watch-list', methods=['POST'])
def add_repo_to_watch_list():
    repo = request.form.get('repos')
    if repo:
        repo_name, owner_login = repo.split(":")
        # Add the repository to the user's watch list...
        repo = Repo(name=repo_name, owner=owner_login, user_id=current_user.id)
        db.session.add(repo)
        db.session.commit()
        #if setup_webhook(current_user, repo_name, owner_login):
        #    flash(f"Added {repo_name} by {owner_login} to watch list")

    return redirect(url_for('views.profile'))

    
