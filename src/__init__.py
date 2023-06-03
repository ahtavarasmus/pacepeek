from flask import Flask
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound
from flask_login import LoginManager, current_user, login_user

import os
from flask_sqlalchemy import SQLAlchemy
import json

with open('/etc/pacepeek_config.json') as config_file:
    config = json.load(config_file)

db = SQLAlchemy()
DB_NAME = config.get('DB_NAME')

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)


    from .auth import auth
    from .views import views 
    from .models import User,Post,OAuth
    blueprint = make_github_blueprint(
        client_id=config.get('GITHUB_CLIENT_ID'),
        client_secret=config.get('GITHUB_CLIENT_SECRET'),
        scope="repo",
        storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
    )

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(blueprint, url_prefix="/login")
    @oauth_authorized.connect_via(blueprint)
    def github_logged_in(blueprint, token):
        github_info = blueprint.session.get("/user")
        if github_info.ok:
            github_user_id = str(github_info.json()["id"])
            query = User.query.filter_by(github_id=github_user_id)
            try:
                user = query.one()
            except NoResultFound:
                user = User(github_id=github_user_id)
                db.session.add(user)
                db.session.commit()
            login_user(user)


    if not os.path.exists(f'src/{DB_NAME}'):
        with app.app_context():
            db.create_all()
        print('Created Database!')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


