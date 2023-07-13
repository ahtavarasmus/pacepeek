from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, render_template_string

from flask_login import login_required, current_user
from requests_oauthlib import OAuth2Session
import requests

from src.github_auth import login
from . import db,config
from .models import User, Repo, Post
from pprint import pprint
from .utils import get_repos,get_next_posts
from .github_utils import handle_payload, setup_webhook
from datetime import datetime
import time


views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        github_login = session.get('search_result')
        user = User.query.filter_by(github_login=github_login).first()
        if user:
            return redirect(f"/profile/{user.github_login}")
        flash("Couldn't find the user")

    if current_user.is_authenticated:
        session['oldest_post_time'] = datetime.utcnow()
        followed_users = current_user.followed.all()
        followed_users_ids = [user.id for user in followed_users]
        #followed_users_ids.append(current_user.id) # include the current user's posts
        posts = Post.query.filter(Post.user_id.in_(followed_users_ids)).order_by(Post.time_stamp.desc()).limit(POSTS_PER_PAGE).all()
    else:
        posts = []

    print("users:",User.query.all())

    return render_template("home.html", user=current_user, posts=posts)

@views.route('/profile/<github_login>')
def profile(github_login=None):
    user = User.query.filter_by(github_login=github_login).first()
    if not user:
        flash("Couldn't find the user")
        return redirect(url_for('views.home'))

    repos = user.repos
    is_following = current_user.is_following(user)
    # getting all the posts from the user that are ready (not_finished=False)
    posts = Post.query.filter_by(user_id=user.id, not_finished=False).all()
        
    return render_template("profile.html", user=user, repos=repos, posts=posts, is_following=is_following)

@login_required
@views.route('/unfollow-<github_login>')
def unfollow(github_login):
    user_to_unfollow = User.query.filter_by(github_login=github_login).first()
    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    return f'''
    <button 
        type="button" 
        class="btn btn-primary" 
        hx-get="/follow-{github_login}" 
        hx-swap="outerHTML">
        Follow
    </button>
    '''

@login_required
@views.route('/follow-<github_login>')
def follow(github_login):
    user_to_follow = User.query.filter_by(github_login=github_login).first()
    current_user.follow(user_to_follow)
    db.session.commit()
    return f'''
    <button 
        type="button" 
        class="btn btn-success" 
        hx-get="/unfollow-{github_login}" 
        hx-swap="outerHTML">
        Following
    </button>
    '''

POSTS_PER_PAGE = 5  # number of posts to load per request

@login_required
@views.route('/load_more_posts')
def load_more_posts():
    # Get page number from URL parameter
    page = request.args.get('page', 1, type=int)

    # Query the database for the next set of posts

    followed_users = current_user.followed.all()
    followed_users_ids = [user.id for user in followed_users]
    #followed_users_ids.append(current_user.id) # include the current user's posts
    next_posts = Post.query.filter(Post.user_id.in_(followed_users_ids), Post.time_stamp < session['oldest_post_time']).order_by(Post.time_stamp.desc()).paginate(page=page, per_page=POSTS_PER_PAGE).items

    
    if next_posts:
        session['oldest_post_time'] = next_posts[-1].time_stamp

    # Render the posts to a string of HTML
    posts_html = render_template('_posts.html', posts=next_posts)
    return render_template_string('<div hx-get="/load_more_posts?page={{page}}" hx-trigger="revealed" hx-swap="beforeend">{{posts_html | safe}}</div>', page=page+1, posts_html=posts_html)


@views.route('/search', methods=['POST'])
def search():
    """
    returns a list of users that match the search term
    """
    search_term = request.form.get('search')
    print("search_term:",search_term)
    users = User.query.filter(User.github_login.like(f"%{search_term}%")).all()
    print("users:",users)
    if users:
        session['search_result'] = users[0].github_login

    return render_template('_search.html', users=users)


@login_required
@views.route('/get-repos',methods=['GET'])
def get_repos_route():
    repos = get_repos(current_user.github_login)
    print("repos:",repos)
    if not repos:
        flash("Couldn't get the user's repositories")
        return redirect(url_for('views.profile', github_login=current_user.github_login))

    repo_options = "\n".join(f'<option value="{name}">{name}</option>' for name in repos)
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
    repo_name = request.form.get('repos')
    owner_github_login = current_user.github_login
    if not repo_name:
        flash("Please select a repository")
        return redirect(url_for('views.profile', github_login=owner_github_login))
    
    hook_id = setup_webhook(current_user, repo_name, owner_github_login)
    print("hook_id",hook_id)
    if hook_id:
        repo = Repo(name=repo_name, webhook_id=hook_id, owner_github_login=owner_github_login, user_id=current_user.id)
        db.session.add(repo)
        db.session.commit()
        flash(f"Added {repo_name} by {owner_github_login} to watch list")
    else:
        flash("Couldn't add the repository to the watch list")
        
    return redirect(f'/profile/{current_user.github_login}')

@login_required
@views.route('/untrack/<owner>/<repo_name>')
def untrack_repo(repo_name, owner):
    repo = Repo.query.filter_by(name=repo_name, owner_github_login=owner).first()
    hook_id = repo.webhook_id
    headers = {'Authorization': f'token ' + session['access_token']}
    response = requests.delete(f'https://api.github.com/repos/{owner}/{repo_name}/hooks/{hook_id}', headers=headers)
    print("response:",response)
    if response.status_code != 204:
        flash("Couldn't remove the repository from the watch list")
        return redirect(f'/profile/{current_user.github_login}')

    db.session.delete(repo)
    db.session.commit()
    flash(f"Removed {repo_name} by {owner} from watch list")

    repos = Repo.query.filter_by(user_id=current_user.id).all()
    return render_template('_repos.html', repos=repos)


@views.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json
    # just checking if push event("after") or ping
    print("hihiH")
    if "after" in payload:
        print("payload:",payload)
        print("haha")
        try:
            handle_payload(payload)
        except:
            pass
    return '', 200
