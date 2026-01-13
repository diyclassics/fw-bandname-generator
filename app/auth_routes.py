from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.models import db, User

# Create auth blueprint
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET'])
def login():
    """Display login page"""
    # If user is already logged in, redirect to index
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))
