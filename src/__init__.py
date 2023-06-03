from flask import Flask
from flask_login import LoginManager

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

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    from .models import User,Post

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


