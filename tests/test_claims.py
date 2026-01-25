"""
Tests for claims functionality.

Day 25: Claims tests covering:
- Claim success
- Claim limit enforcement (max 5)
- Duplicate claim prevention
- Unclaim functionality
- Authorization checks
"""

import pytest
import json
from app.models import db, User, ClaimedBandName


class TestClaimBand:
    """Tests for claiming band names."""

    def test_claim_success(self, logged_in_client, app):
        """Test successful band name claim."""
        client, user_id = logged_in_client
        response = client.post('/user/claim',
            data=json.dumps({'band_name': 'The Wandering Echoes'}),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'claim_id' in data

        # Verify claim was created in database
        with app.app_context():
            claim = ClaimedBandName.query.filter_by(band_name_lower='the wandering echoes').first()
            assert claim is not None
            assert claim.user_id == user_id

    def test_claim_requires_login(self, client, app):
        """Test claim endpoint requires authentication."""
        response = client.post('/user/claim',
            data=json.dumps({'band_name': 'Test Band'}),
            content_type='application/json'
        )

        # Should redirect to login
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_claim_requires_band_name(self, logged_in_client, app):
        """Test claim fails without band name."""
        client, user_id = logged_in_client
        response = client.post('/user/claim',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_claim_empty_band_name(self, logged_in_client, app):
        """Test claim fails with empty band name."""
        client, user_id = logged_in_client
        response = client.post('/user/claim',
            data=json.dumps({'band_name': '   '}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'Band name is required' in data['error']

    def test_claim_invalid_json(self, logged_in_client, app):
        """Test claim fails with invalid JSON."""
        client, user_id = logged_in_client
        response = client.post('/user/claim',
            data='not json',
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_claim_duplicate_prevention(self, logged_in_client, app):
        """Test cannot claim already claimed band name."""
        client, user_id = logged_in_client

        # First claim
        client.post('/user/claim',
            data=json.dumps({'band_name': 'Unique Band Name'}),
            content_type='application/json'
        )

        # Create second user and try to claim same band
        with app.app_context():
            user2 = User(username='seconduser', email='second@example.com')
            user2.set_password('password123')
            db.session.add(user2)
            db.session.commit()
            user2_id = user2.id

        # Login as second user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user2_id)
            sess['_fresh'] = True

        # Try to claim same band
        response = client.post('/user/claim',
            data=json.dumps({'band_name': 'Unique Band Name'}),
            content_type='application/json'
        )

        assert response.status_code == 409  # Conflict
        data = response.get_json()
        assert 'Already claimed' in data['error']

    def test_claim_duplicate_case_insensitive(self, logged_in_client, app):
        """Test duplicate detection is case-insensitive."""
        client, user_id = logged_in_client

        # First claim lowercase
        client.post('/user/claim',
            data=json.dumps({'band_name': 'case test band'}),
            content_type='application/json'
        )

        # Create second user
        with app.app_context():
            user2 = User(username='user2', email='user2@example.com')
            user2.set_password('password123')
            db.session.add(user2)
            db.session.commit()
            user2_id = user2.id

        # Login as second user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user2_id)
            sess['_fresh'] = True

        # Try to claim same band with different case
        response = client.post('/user/claim',
            data=json.dumps({'band_name': 'CASE TEST BAND'}),
            content_type='application/json'
        )

        assert response.status_code == 409

    def test_claim_limit_enforcement(self, client, app, user_at_claim_limit):
        """Test user cannot exceed 5-claim limit."""
        user_id, claim_ids = user_at_claim_limit

        # Login as user at limit
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True

        response = client.post('/user/claim',
            data=json.dumps({'band_name': 'One More Band'}),
            content_type='application/json'
        )

        assert response.status_code == 403
        data = response.get_json()
        assert 'Maximum 5 claims' in data['error']

    def test_claim_real_band_rejected(self, logged_in_client, app):
        """Test cannot claim actual band names from bands.txt."""
        client, user_id = logged_in_client

        # "U2" and "Tame Impala" are in bands.txt
        response = client.post('/user/claim',
            data=json.dumps({'band_name': 'U2'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'real band name' in data['error']

    def test_claim_real_band_rejected_case_insensitive(self, logged_in_client, app):
        """Test real band check is case-insensitive."""
        client, user_id = logged_in_client

        # "tame impala" with different case should still be rejected
        response = client.post('/user/claim',
            data=json.dumps({'band_name': 'TAME IMPALA'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'real band name' in data['error']


class TestUnclaimBand:
    """Tests for unclaiming band names."""

    def test_unclaim_success(self, logged_in_client, app):
        """Test successful unclaim."""
        client, user_id = logged_in_client

        # First create a claim
        with app.app_context():
            claim = ClaimedBandName(
                user_id=user_id,
                band_name='To Be Released',
                band_name_lower='to be released'
            )
            db.session.add(claim)
            db.session.commit()
            claim_id = claim.id

        # Unclaim it
        response = client.post(f'/user/unclaim/{claim_id}', follow_redirects=True)

        assert response.status_code == 200
        assert b'Released' in response.data

        # Verify claim was deleted
        with app.app_context():
            assert ClaimedBandName.query.get(claim_id) is None

    def test_unclaim_requires_login(self, client, app, sample_user_with_claims):
        """Test unclaim requires authentication."""
        user_id, claim_ids = sample_user_with_claims

        response = client.post(f'/user/unclaim/{claim_ids[0]}')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_unclaim_only_own_claims(self, logged_in_client, app):
        """Test user can only unclaim their own bands."""
        client, user_id = logged_in_client

        # Create another user with a claim
        with app.app_context():
            other_user = User(username='other', email='other@example.com')
            other_user.set_password('password123')
            db.session.add(other_user)
            db.session.commit()

            other_claim = ClaimedBandName(
                user_id=other_user.id,
                band_name='Other User Band',
                band_name_lower='other user band'
            )
            db.session.add(other_claim)
            db.session.commit()
            other_claim_id = other_claim.id

        # Try to unclaim other user's band
        response = client.post(f'/user/unclaim/{other_claim_id}', follow_redirects=True)

        assert response.status_code == 200
        assert b'only unclaim your own' in response.data

        # Verify claim still exists
        with app.app_context():
            assert ClaimedBandName.query.get(other_claim_id) is not None

    def test_unclaim_nonexistent_claim(self, logged_in_client, app):
        """Test unclaim returns 404 for non-existent claim."""
        client, user_id = logged_in_client

        response = client.post('/user/unclaim/99999')
        assert response.status_code == 404


class TestDashboard:
    """Tests for user dashboard."""

    def test_dashboard_requires_login(self, client, app):
        """Test dashboard requires authentication."""
        response = client.get('/user/dashboard')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_dashboard_shows_claims(self, logged_in_client, app):
        """Test dashboard displays user's claimed bands."""
        client, user_id = logged_in_client

        # Create some claims
        with app.app_context():
            for name in ['Band One', 'Band Two']:
                claim = ClaimedBandName(
                    user_id=user_id,
                    band_name=name,
                    band_name_lower=name.lower()
                )
                db.session.add(claim)
            db.session.commit()

        response = client.get('/user/dashboard')

        assert response.status_code == 200
        assert b'Band One' in response.data
        assert b'Band Two' in response.data

    def test_dashboard_shows_claim_count(self, logged_in_client, app):
        """Test dashboard shows claim count."""
        client, user_id = logged_in_client

        # Create 2 claims
        with app.app_context():
            for i in range(2):
                claim = ClaimedBandName(
                    user_id=user_id,
                    band_name=f'Count Band {i}',
                    band_name_lower=f'count band {i}'
                )
                db.session.add(claim)
            db.session.commit()

        response = client.get('/user/dashboard')

        assert response.status_code == 200
        # Should show "2/5" or similar
        assert b'2' in response.data
        assert b'5' in response.data

    def test_dashboard_empty_state(self, logged_in_client, app):
        """Test dashboard with no claims."""
        client, user_id = logged_in_client

        response = client.get('/user/dashboard')

        assert response.status_code == 200
        # Should show 0 claims
        assert b'0' in response.data
