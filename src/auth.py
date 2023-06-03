from flask import Blueprint, render_template, redirect, url_for, request, flash

from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .models import User
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()
        except:
            user = None
        if user:
            flash('Username already exists.', category='error')
        #elif not password or len(password) < 7:
        #    flash('Password must be at least 7 characters.', category='error')
        elif not password:
            flash('give password pls', category='error')
        else:
            new_user = User(username=username, password=generate_password_hash(password, method='scrypt'))
            db.session.add(new_user)
            db.session.commit()
            flash('Account created!', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()
        except:
            user = None
    
        if user:
            if password and check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Username does not exist.', category='error')

    return render_template("login.html", user=current_user)

@login_required
@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


