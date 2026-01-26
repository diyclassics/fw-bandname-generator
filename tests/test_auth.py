"""
Tests for authentication routes.

Day 25: Auth tests covering:
- User registration (success, validation, duplicates)
- Login (success, invalid credentials)
- Logout
- Redirect behavior
"""

import pytest
from app.models import db, User


class TestRegistration:
    """Tests for user registration."""

    def test_register_page_loads(self, client, app):
        """Test registration page renders correctly."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Register' in response.data

    def test_register_success(self, client, app):
        """Test successful user registration."""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Registration successful' in response.data

        # Verify user was created
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'newuser@example.com'
            assert user.check_password('securepassword123')

    def test_register_missing_username(self, client, app):
        """Test registration fails without username."""
        response = client.post('/auth/register', data={
            'username': '',
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })

        assert response.status_code == 200
        assert b'Username is required' in response.data

    def test_register_username_too_short(self, client, app):
        """Test registration fails with short username."""
        response = client.post('/auth/register', data={
            'username': 'ab',
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })

        assert response.status_code == 200
        assert b'at least 3 characters' in response.data

    def test_register_missing_email(self, client, app):
        """Test registration fails without email."""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': '',
            'password': 'password123',
            'password_confirm': 'password123'
        })

        assert response.status_code == 200
        assert b'Email is required' in response.data

    def test_register_missing_password(self, client, app):
        """Test registration fails without password."""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '',
            'password_confirm': ''
        })

        assert response.status_code == 200
        assert b'Password is required' in response.data

    def test_register_password_too_short(self, client, app):
        """Test registration fails with short password."""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short',
            'password_confirm': 'short'
        })

        assert response.status_code == 200
        assert b'at least 8 characters' in response.data

    def test_register_password_mismatch(self, client, app):
        """Test registration fails when passwords don't match."""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'differentpass'
        })

        assert response.status_code == 200
        assert b'Passwords do not match' in response.data

    def test_register_duplicate_username(self, client, app, sample_user):
        """Test registration fails with existing username."""
        response = client.post('/auth/register', data={
            'username': 'testuser',  # Already exists from sample_user
            'email': 'different@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })

        assert response.status_code == 200
        assert b'Username already taken' in response.data

    def test_register_duplicate_email(self, client, app, sample_user):
        """Test registration fails with existing email."""
        response = client.post('/auth/register', data={
            'username': 'differentuser',
            'email': 'test@example.com',  # Already exists from sample_user
            'password': 'password123',
            'password_confirm': 'password123'
        })

        assert response.status_code == 200
        assert b'Email already registered' in response.data

    def test_register_redirects_if_logged_in(self, logged_in_client, app):
        """Test registration page redirects when user is logged in."""
        client, user_id = logged_in_client
        response = client.get('/auth/register')
        assert response.status_code == 302


class TestLogin:
    """Tests for user login."""

    def test_login_page_loads(self, client, app):
        """Test login page renders correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_login_success(self, client, app, sample_user):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Welcome back' in response.data

    def test_login_invalid_email(self, client, app, sample_user):
        """Test login fails with non-existent email."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })

        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_invalid_password(self, client, app, sample_user):
        """Test login fails with wrong password."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })

        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_empty_fields(self, client, app):
        """Test login fails with empty fields."""
        response = client.post('/auth/login', data={
            'email': '',
            'password': ''
        })

        assert response.status_code == 200
        assert b'Email and password are required' in response.data

    def test_login_redirects_if_logged_in(self, logged_in_client, app):
        """Test login page redirects when user is logged in."""
        client, user_id = logged_in_client
        response = client.get('/auth/login')
        assert response.status_code == 302

    def test_login_with_remember_me(self, client, app, sample_user):
        """Test login with 'remember me' checkbox."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123',
            'remember': 'on'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Welcome back' in response.data


class TestLogout:
    """Tests for user logout."""

    def test_logout_success(self, logged_in_client, app):
        """Test successful logout."""
        client, user_id = logged_in_client
        response = client.get('/auth/logout', follow_redirects=True)

        assert response.status_code == 200
        assert b'logged out' in response.data

    def test_logout_requires_login(self, client, app):
        """Test logout redirects to login when not logged in."""
        response = client.get('/auth/logout')
        assert response.status_code == 302
        assert '/auth/login' in response.location


class TestOAuthRoutes:
    """Tests for OAuth route handling (without actual OAuth flow)."""

    def test_google_oauth_not_configured(self, client, app):
        """Test Google OAuth shows warning when not configured."""
        # Testing config doesn't have OAuth credentials
        response = client.get('/auth/oauth/google', follow_redirects=True)
        assert response.status_code == 200
        assert b'not configured' in response.data

    def test_github_oauth_not_configured(self, client, app):
        """Test GitHub OAuth shows warning when not configured."""
        response = client.get('/auth/oauth/github', follow_redirects=True)
        assert response.status_code == 200
        assert b'not configured' in response.data

    def test_google_oauth_redirect_if_logged_in(self, logged_in_client, app):
        """Test Google OAuth redirects when user is logged in."""
        client, user_id = logged_in_client
        response = client.get('/auth/oauth/google')
        assert response.status_code == 302

    def test_github_oauth_redirect_if_logged_in(self, logged_in_client, app):
        """Test GitHub OAuth redirects when user is logged in."""
        client, user_id = logged_in_client
        response = client.get('/auth/oauth/github')
        assert response.status_code == 302


class TestRegistrationDisabled:
    """Tests for registration disabled feature."""

    def test_register_disabled_redirects_get(self, client, app):
        """Test GET to register page redirects when registration is disabled."""
        app.config['REGISTRATION_ENABLED'] = False
        response = client.get('/auth/register', follow_redirects=True)

        assert response.status_code == 200
        assert b'Registration is currently closed' in response.data

    def test_register_disabled_redirects_post(self, client, app):
        """Test POST to register is rejected when registration is disabled."""
        app.config['REGISTRATION_ENABLED'] = False
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Registration is currently closed' in response.data

        # Verify user was NOT created
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is None

    def test_login_page_hides_register_link_when_disabled(self, client, app):
        """Test login page hides 'Create one' link when registration is disabled."""
        app.config['REGISTRATION_ENABLED'] = False
        response = client.get('/auth/login')

        assert response.status_code == 200
        assert b'Create one' not in response.data

    def test_login_page_shows_register_link_when_enabled(self, client, app):
        """Test login page shows 'Create one' link when registration is enabled."""
        app.config['REGISTRATION_ENABLED'] = True
        response = client.get('/auth/login')

        assert response.status_code == 200
        assert b'Create one' in response.data

    def test_existing_user_can_login_when_registration_disabled(self, client, app, sample_user):
        """Test existing users can still log in when registration is disabled."""
        app.config['REGISTRATION_ENABLED'] = False
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Welcome back' in response.data
