from . import db
from flask_login import UserMixin


class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150),nullable=True)
    github_token = db.Column(db.String(500),nullable=True)
    posts = db.relationship('Post', backref='user')
    repos = db.relationship('Repo', backref='user')

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r' % self.username

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repo = db.Column(db.String(300))
    text = db.Column(db.String)
    not_finished = db.Column(db.Boolean, default=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    commits = db.relationship('Commit', backref='post')

    def __repr__(self):
        return '<Post %r' % self.id

class Commit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sha = db.Column(db.String(300))
    message = db.Column(db.String(300))
    link = db.Column(db.String(300))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    patches = db.relationship('Patch', backref='commit')

    def __repr__(self):
        return '<Commit %r' % self.id
class Patch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300))
    patch_body = db.Column(db.String(300))
    commit_id = db.Column(db.Integer, db.ForeignKey('commit.id'))

    def __repr__(self):
        return '<Patch %r' % self.id

class Repo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    owner = db.Column(db.String(300))
    latest_commit_sha = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Repo %r' % self.id
