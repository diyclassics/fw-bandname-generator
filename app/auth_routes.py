from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.models import db, User
from app.auth import oauth

# Create auth blueprint
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Display login page and handle login"""
    # If user is already logged in, redirect to index
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('auth/login.html', email=email)

        # Find user by email
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', email=email)

        # Login successful
        login_user(user, remember=bool(remember))
        flash(f'Welcome back, {user.username}!', 'success')

        # Redirect to next page or index
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main_bp.index'))

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    # Check if registration is enabled
    if not current_app.config.get('REGISTRATION_ENABLED', True):
        flash('Registration is currently closed.', 'warning')
        return redirect(url_for('auth_bp.login'))

    # If user is already logged in, redirect to index
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Validation
        errors = []

        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        elif len(username) > 80:
            errors.append('Username must be 80 characters or less.')

        if not email:
            errors.append('Email is required.')

        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        if password != password_confirm:
            errors.append('Passwords do not match.')

        # Check for existing username/email
        if not errors:
            if User.query.filter_by(username=username).first():
                errors.append('Username already taken.')
            if User.query.filter_by(email=email).first():
                errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html',
                                   username=username,
                                   email=email)

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth_bp.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))


# =============================================================================
# OAuth Routes
# =============================================================================

@auth_bp.route('/oauth/google')
def oauth_google():
    """Initiate Google OAuth flow"""
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))

    # Check if Google OAuth is configured
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        flash('Google login is not configured.', 'warning')
        return redirect(url_for('auth_bp.login'))

    redirect_uri = url_for('auth_bp.oauth_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/oauth/google/callback')
def oauth_google_callback():
    """Handle Google OAuth callback"""
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            # Fetch user info if not in token
            user_info = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo').json()

    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {e}')
        flash('Failed to authenticate with Google.', 'danger')
        return redirect(url_for('auth_bp.login'))

    # Extract user data from Google
    google_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name')
    picture = user_info.get('picture')

    if not google_id or not email:
        flash('Could not retrieve account information from Google.', 'danger')
        return redirect(url_for('auth_bp.login'))

    # Find or create user
    user = User.query.filter_by(oauth_provider='google', oauth_id=google_id).first()

    if not user:
        # Check if email already exists (maybe registered with password)
        user = User.query.filter_by(email=email).first()

        if user:
            # Link Google account to existing user
            user.oauth_provider = 'google'
            user.oauth_id = google_id
            if picture and not user.avatar_url:
                user.avatar_url = picture
        else:
            # Check if registration is enabled before creating new user
            if not current_app.config.get('REGISTRATION_ENABLED', True):
                flash('Registration is currently closed. Only existing users can log in.', 'warning')
                return redirect(url_for('auth_bp.login'))

            # Create new user
            # Generate unique username from email
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f'{base_username}{counter}'
                counter += 1

            user = User(
                username=username,
                email=email,
                oauth_provider='google',
                oauth_id=google_id,
                display_name=name,
                avatar_url=picture,
            )
            db.session.add(user)

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Log the user in
    login_user(user, remember=True)
    flash(f'Welcome, {user.display_name or user.username}!', 'success')

    return redirect(url_for('main_bp.index'))


@auth_bp.route('/oauth/github')
def oauth_github():
    """Initiate GitHub OAuth flow"""
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))

    # Check if GitHub OAuth is configured
    if not current_app.config.get('GITHUB_CLIENT_ID'):
        flash('GitHub login is not configured.', 'warning')
        return redirect(url_for('auth_bp.login'))

    redirect_uri = url_for('auth_bp.oauth_github_callback', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@auth_bp.route('/oauth/github/callback')
def oauth_github_callback():
    """Handle GitHub OAuth callback"""
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))

    try:
        token = oauth.github.authorize_access_token()

        # Fetch user profile from GitHub API
        resp = oauth.github.get('user', token=token)
        user_info = resp.json()

        # Fetch user's email (may be private)
        email = user_info.get('email')
        if not email:
            # Try to get email from emails endpoint
            emails_resp = oauth.github.get('user/emails', token=token)
            emails = emails_resp.json()
            # Find primary verified email
            for e in emails:
                if e.get('primary') and e.get('verified'):
                    email = e.get('email')
                    break

    except Exception as e:
        current_app.logger.error(f'GitHub OAuth error: {e}')
        flash('Failed to authenticate with GitHub.', 'danger')
        return redirect(url_for('auth_bp.login'))

    # Extract user data from GitHub
    github_id = str(user_info.get('id'))
    username_from_github = user_info.get('login')
    name = user_info.get('name') or username_from_github
    avatar = user_info.get('avatar_url')

    if not github_id:
        flash('Could not retrieve account information from GitHub.', 'danger')
        return redirect(url_for('auth_bp.login'))

    # Find or create user
    user = User.query.filter_by(oauth_provider='github', oauth_id=github_id).first()

    if not user:
        # Check if email already exists (maybe registered with password or Google)
        if email:
            user = User.query.filter_by(email=email).first()

        if user:
            # Link GitHub account to existing user
            user.oauth_provider = 'github'
            user.oauth_id = github_id
            if avatar and not user.avatar_url:
                user.avatar_url = avatar
        else:
            # Check if registration is enabled before creating new user
            if not current_app.config.get('REGISTRATION_ENABLED', True):
                flash('Registration is currently closed. Only existing users can log in.', 'warning')
                return redirect(url_for('auth_bp.login'))

            # Create new user
            # Try to use GitHub username, or generate unique one
            username = username_from_github
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f'{username_from_github}{counter}'
                counter += 1

            user = User(
                username=username,
                email=email,  # May be None if user has no public email
                oauth_provider='github',
                oauth_id=github_id,
                display_name=name,
                avatar_url=avatar,
            )
            db.session.add(user)

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Log the user in
    login_user(user, remember=True)
    flash(f'Welcome, {user.display_name or user.username}!', 'success')

    return redirect(url_for('main_bp.index'))
