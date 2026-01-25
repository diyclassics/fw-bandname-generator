"""
Tests for database models (User and ClaimedBandName).

Day 24: Model tests covering:
- Password hashing and verification
- Claim limit enforcement
- Band name normalization
- Model relationships
"""

import pytest
from app.models import db, User, ClaimedBandName


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app):
        """Test basic user creation."""
        with app.app_context():
            user = User(username='newuser', email='new@example.com')
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == 'newuser'
            assert user.email == 'new@example.com'
            assert user.created_at is not None

    def test_user_repr(self, app):
        """Test User string representation."""
        with app.app_context():
            user = User(username='repruser', email='repr@example.com')
            db.session.add(user)
            db.session.commit()

            assert repr(user) == '<User repruser>'

    def test_set_password_hashes_password(self, app):
        """Test that set_password stores a hash, not plaintext."""
        with app.app_context():
            user = User(username='hashtest', email='hash@example.com')
            user.set_password('mypassword123')
            db.session.add(user)
            db.session.commit()

            assert user.password_hash is not None
            assert user.password_hash != 'mypassword123'
            assert len(user.password_hash) > 50  # Hash should be longer than password

    def test_check_password_correct(self, app, sample_user):
        """Test password verification with correct password."""
        with app.app_context():
            user = User.query.get(sample_user)
            assert user.check_password('password123') is True

    def test_check_password_incorrect(self, app, sample_user):
        """Test password verification with incorrect password."""
        with app.app_context():
            user = User.query.get(sample_user)
            assert user.check_password('wrongpassword') is False

    def test_check_password_empty(self, app, sample_user):
        """Test password verification with empty password."""
        with app.app_context():
            user = User.query.get(sample_user)
            assert user.check_password('') is False

    def test_check_password_no_hash(self, app):
        """Test check_password returns False when no password hash is set (OAuth users)."""
        with app.app_context():
            user = User(
                username='oauthuser',
                email='oauth@example.com',
                oauth_provider='google',
                oauth_id='12345'
            )
            db.session.add(user)
            db.session.commit()

            # OAuth user has no password hash
            assert user.password_hash is None
            assert user.check_password('anypassword') is False

    def test_can_claim_new_user(self, app, sample_user):
        """Test that new user without claims can claim."""
        with app.app_context():
            user = User.query.get(sample_user)
            assert user.can_claim is True

    def test_can_claim_with_some_claims(self, app, sample_user_with_claims):
        """Test user with 3 claims can still claim more."""
        user_id, claim_ids = sample_user_with_claims
        with app.app_context():
            user = User.query.get(user_id)
            assert user.claimed_bands.count() == 3
            assert user.can_claim is True

    def test_can_claim_at_limit(self, app, user_at_claim_limit):
        """Test user at 5-claim limit cannot claim more."""
        user_id, claim_ids = user_at_claim_limit
        with app.app_context():
            user = User.query.get(user_id)
            assert user.claimed_bands.count() == 5
            assert user.can_claim is False

    def test_username_unique_constraint(self, app, sample_user):
        """Test that duplicate usernames are rejected."""
        with app.app_context():
            duplicate = User(username='testuser', email='different@example.com')
            db.session.add(duplicate)
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_email_unique_constraint(self, app, sample_user):
        """Test that duplicate emails are rejected."""
        with app.app_context():
            duplicate = User(username='differentuser', email='test@example.com')
            db.session.add(duplicate)
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_cascade_delete_claims(self, app, sample_user_with_claims):
        """Test that deleting a user deletes their claims."""
        user_id, claim_ids = sample_user_with_claims
        with app.app_context():
            user = User.query.get(user_id)
            db.session.delete(user)
            db.session.commit()

            # Claims should be deleted
            for claim_id in claim_ids:
                assert ClaimedBandName.query.get(claim_id) is None


class TestClaimedBandNameModel:
    """Tests for the ClaimedBandName model."""

    def test_create_claim(self, app, sample_user):
        """Test basic claim creation."""
        with app.app_context():
            claim = ClaimedBandName(
                user_id=sample_user,
                band_name='The Test Band',
                band_name_lower='the test band'
            )
            db.session.add(claim)
            db.session.commit()

            assert claim.id is not None
            assert claim.band_name == 'The Test Band'
            assert claim.band_name_lower == 'the test band'
            assert claim.claimed_at is not None

    def test_claim_repr(self, app, sample_user):
        """Test ClaimedBandName string representation."""
        with app.app_context():
            claim = ClaimedBandName(
                user_id=sample_user,
                band_name='Repr Band',
                band_name_lower='repr band'
            )
            db.session.add(claim)
            db.session.commit()

            assert f"<ClaimedBandName 'Repr Band' by User {sample_user}>" == repr(claim)

    def test_normalize_name_lowercase(self):
        """Test normalize_name converts to lowercase."""
        assert ClaimedBandName.normalize_name('The Beatles') == 'the beatles'

    def test_normalize_name_strips_whitespace(self):
        """Test normalize_name strips leading/trailing whitespace."""
        assert ClaimedBandName.normalize_name('  Pink Floyd  ') == 'pink floyd'

    def test_normalize_name_preserves_internal_spaces(self):
        """Test normalize_name preserves internal spaces."""
        assert ClaimedBandName.normalize_name('Led Zeppelin') == 'led zeppelin'

    def test_normalize_name_empty_string(self):
        """Test normalize_name handles empty strings."""
        assert ClaimedBandName.normalize_name('') == ''

    def test_normalize_name_whitespace_only(self):
        """Test normalize_name handles whitespace-only strings."""
        assert ClaimedBandName.normalize_name('   ') == ''

    def test_band_name_lower_unique_constraint(self, app, sample_user):
        """Test that duplicate normalized band names are rejected."""
        with app.app_context():
            # Create first claim
            claim1 = ClaimedBandName(
                user_id=sample_user,
                band_name='Unique Band',
                band_name_lower='unique band'
            )
            db.session.add(claim1)
            db.session.commit()

            # Try to create duplicate
            claim2 = ClaimedBandName(
                user_id=sample_user,
                band_name='UNIQUE BAND',  # Same name, different case
                band_name_lower='unique band'  # Same normalized
            )
            db.session.add(claim2)
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_claim_relationship_to_user(self, app, sample_user_with_claims):
        """Test claim.user relationship returns correct user."""
        user_id, claim_ids = sample_user_with_claims
        with app.app_context():
            claim = ClaimedBandName.query.get(claim_ids[0])
            assert claim.user.id == user_id
            assert claim.user.username == 'testuser'

    def test_user_claimed_bands_relationship(self, app, sample_user_with_claims):
        """Test user.claimed_bands relationship returns all claims."""
        user_id, claim_ids = sample_user_with_claims
        with app.app_context():
            user = User.query.get(user_id)
            claims = user.claimed_bands.all()

            assert len(claims) == 3
            claim_band_names = [c.band_name for c in claims]
            assert 'The Wandering Echoes' in claim_band_names
            assert 'Silent Thunder' in claim_band_names
            assert 'Midnight Reverie' in claim_band_names
