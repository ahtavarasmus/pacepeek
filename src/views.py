from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, render_template_string

from flask_login import login_required, current_user
from requests_oauthlib import OAuth2Session

from src.github_auth import login
from . import db,config
from .models import User, Repo, Post
from pprint import pprint
from .utils import get_repos,get_next_posts
from .github_utils import handle_payload, setup_webhook
from datetime import datetime
import time


views = Blueprint('views', __name__)


@login_required
@views.route('/', methods=['GET', 'POST'])
def home():
    session['oldest_post_time'] = datetime.utcnow()
    posts = get_next_posts()
    return render_template("home.html", user=current_user,posts=posts)

@login_required
@views.route('/profile/<login>')
def profile(login):
    if current_user.login == login:
        user = current_user
    else:
        user = User.query.filter_by(login=login).first()

    repos = user.repos
    # getting all the posts from the user that are ready (not_finished=False)
    posts = Post.query.filter_by(user_id=user.id, not_finished=False).all()
        
    return render_template("profile.html", user=user, repos=repos, posts=posts)


@login_required
@views.route('/load_more_posts')
def load_more_posts():
    # Get the next set of posts 
    next_posts = get_next_posts()

    # Render the posts to a string of HTML
    posts_html = render_template_string('_posts.html', posts=next_posts)

    return posts_html


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
        # Add the repository to the user's watch list
        if setup_webhook(current_user, repo_name, owner_login):
            repo = Repo(name=repo_name, owner=owner_login, user_id=current_user.id)
            db.session.add(repo)
            db.session.commit()
            flash(f"Added {repo_name} by {owner_login} to watch list")
        else:
            repo = Repo.query.filter_by(name=repo_name, owner=owner_login, user_id=current_user.id).first()
            if not repo:
                repo = Repo(name=repo_name, owner=owner_login, user_id=current_user.id)
                db.session.add(repo)
                db.session.commit()
                flash(f"Added {repo_name} by {owner_login} to watch list")


    return redirect(url_for('views.profile'))

@views.route('/payload', methods=['POST'])
def payload():
    payload = request.get_json()
    handle_payload(payload)
    return '', 204

   
