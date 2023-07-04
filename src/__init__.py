from flask import Flask
from sqlalchemy.orm.exc import NoResultFound
from flask_login import LoginManager, current_user, login_user
from flask_migrate import Migrate

import os
from flask_sqlalchemy import SQLAlchemy
import json

with open('/etc/pacepeek_config.json') as config_file:
    config = json.load(config_file)

db = SQLAlchemy()
DB_NAME = config.get('DB_NAME')

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app,db)


    from .views import views 
    from .models import User,Post
    from .github_auth import github_auth
    

    app.register_blueprint(views)
    app.register_blueprint(github_auth)

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


