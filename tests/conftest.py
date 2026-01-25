"""
Pytest fixtures for the Finnegans Wake Band Name Generator tests.

Provides:
- Flask app with testing configuration
- Test client
- Database session management
- Sample user fixtures
"""

import pytest
from app import create_app
from app.models import db, User, ClaimedBandName


@pytest.fixture(scope='function')
def app():
    """
    Create Flask application configured for testing.

    Uses in-memory SQLite database that's created fresh for each test.
    """
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Application context for database operations."""
    with app.app_context():
        yield


@pytest.fixture
def sample_user(app):
    """
    Create a sample user for testing.

    Returns a user with:
    - username: testuser
    - email: test@example.com
    - password: password123
    """
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Refresh to get the id
        db.session.refresh(user)
        user_id = user.id

    # Return user_id so tests can query fresh instance
    return user_id


@pytest.fixture
def sample_user_with_claims(app, sample_user):
    """
    Create a sample user with 3 claimed band names.

    Returns tuple of (user_id, list of claim_ids)
    """
    with app.app_context():
        user = User.query.get(sample_user)

        claims = []
        for i, name in enumerate(['The Wandering Echoes', 'Silent Thunder', 'Midnight Reverie']):
            claim = ClaimedBandName(
                user_id=user.id,
                band_name=name,
                band_name_lower=ClaimedBandName.normalize_name(name)
            )
            db.session.add(claim)
            db.session.commit()
            claims.append(claim.id)

    return sample_user, claims


@pytest.fixture
def user_at_claim_limit(app):
    """
    Create a user who has reached the 5-claim limit.

    Returns tuple of (user_id, list of claim_ids)
    """
    with app.app_context():
        user = User(username='maxclaimuser', email='max@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        claims = []
        for i in range(5):
            claim = ClaimedBandName(
                user_id=user.id,
                band_name=f'Claimed Band {i+1}',
                band_name_lower=f'claimed band {i+1}'
            )
            db.session.add(claim)
            db.session.commit()
            claims.append(claim.id)

        user_id = user.id

    return user_id, claims


@pytest.fixture
def logged_in_client(client, app, sample_user):
    """
    Test client with a logged-in user session.

    Returns tuple of (client, user_id)
    """
    with app.app_context():
        user = User.query.get(sample_user)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client, sample_user
