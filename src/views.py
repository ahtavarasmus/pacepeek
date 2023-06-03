from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_required, current_user

views = Blueprint('views', __name__)


@login_required
@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html", user=current_user)
