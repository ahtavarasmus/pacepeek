from . import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.sql import func

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    github_id = db.Column(db.String(120), unique=True, nullable=False)
    github_login = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(150),nullable=True)
    posts = db.relationship('Post', backref='user')
    repos = db.relationship('Repo', backref='user')
    is_active = db.Column(db.Boolean, default=True, nullable=False)


    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0


    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r' % self.name


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repo = db.Column(db.String(300))
    text = db.Column(db.String)
    not_finished = db.Column(db.Boolean, default=True, nullable=False)
    time_stamp = db.Column(db.DateTime(timezone=True), server_default=func.now())

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
    owner_github_login = db.Column(db.String(300))
    webhook_id = db.Column(db.Integer)
    latest_commit_sha = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Repo %r' % self.id
