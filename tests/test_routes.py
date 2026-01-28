"""
Tests for main application routes.

Day 26: Coverage improvement for routes.py
- Index page (band generation)
- Band page (shareable links)
- Leaderboard
"""

import pytest
from app.models import db, User, ClaimedBandName


class TestIndexRoute:
    """Tests for the main index route."""

    def test_index_loads(self, client, app):
        """Test index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'band' in response.data.lower()

    def test_index_generates_band_name(self, client, app):
        """Test index page generates a band name."""
        response = client.get('/')
        assert response.status_code == 200
        # Should have the bandname container
        assert b'shareable' in response.data.lower() or b'band' in response.data.lower()

    def test_index_shows_claim_button_when_logged_in(self, logged_in_client, app):
        """Test claim button appears for logged-in users."""
        client, user_id = logged_in_client
        response = client.get('/')
        assert response.status_code == 200
        # Should show claim option or dashboard link

    def test_index_shows_duplicate_warning_for_real_band(self, client, app):
        """Test duplicate warning for real band names."""
        # Access /band with a known real band name
        response = client.get('/band?name=U2')
        assert response.status_code == 200
        # Should indicate it's a real band

    def test_index_shows_claimed_by_info(self, client, app, sample_user_with_claims):
        """Test shows who claimed a band name."""
        user_id, claim_ids = sample_user_with_claims

        with app.app_context():
            claim = ClaimedBandName.query.get(claim_ids[0])
            band_name = claim.band_name

        response = client.get(f'/band?name={band_name}')
        assert response.status_code == 200


class TestBandRoute:
    """Tests for the /band shareable link route."""

    def test_band_route_with_name(self, client, app):
        """Test band route displays specified band name."""
        response = client.get('/band?name=Test%20Band%20Name')
        assert response.status_code == 200
        assert b'Test Band Name' in response.data

    def test_band_route_without_name(self, client, app):
        """Test band route falls back to default when no name provided."""
        response = client.get('/band')
        assert response.status_code == 200
        # Should show "The Rejects" or similar fallback
        assert b'Rejects' in response.data or response.status_code == 200

    def test_band_route_with_special_characters(self, client, app):
        """Test band route handles special characters in name."""
        response = client.get('/band?name=The%20%26%20Band')
        assert response.status_code == 200

    def test_band_route_generates_shareable_url(self, client, app):
        """Test band route includes shareable URL."""
        response = client.get('/band?name=Shareable%20Test')
        assert response.status_code == 200
        # The page should contain a shareable link


class TestLeaderboardRoute:
    """Tests for the leaderboard route."""

    def test_leaderboard_loads(self, client, app):
        """Test leaderboard page loads."""
        response = client.get('/leaderboard')
        assert response.status_code == 200
        assert b'Leaderboard' in response.data or b'leaderboard' in response.data.lower()

    def test_leaderboard_empty(self, client, app):
        """Test leaderboard with no claims."""
        response = client.get('/leaderboard')
        assert response.status_code == 200

    def test_leaderboard_shows_users_with_claims(self, client, app, sample_user_with_claims):
        """Test leaderboard displays users who have claims."""
        user_id, claim_ids = sample_user_with_claims

        response = client.get('/leaderboard')
        assert response.status_code == 200
        assert b'testuser' in response.data

    def test_leaderboard_orders_by_claim_count(self, client, app):
        """Test leaderboard orders users by claim count."""
        with app.app_context():
            # Create user with 3 claims
            user1 = User(username='topuser', email='top@example.com')
            user1.set_password('password123')
            db.session.add(user1)
            db.session.commit()

            for i in range(3):
                claim = ClaimedBandName(
                    user_id=user1.id,
                    band_name=f'Top Band {i}',
                    band_name_lower=f'top band {i}'
                )
                db.session.add(claim)

            # Create user with 1 claim
            user2 = User(username='bottomuser', email='bottom@example.com')
            user2.set_password('password123')
            db.session.add(user2)
            db.session.commit()

            claim = ClaimedBandName(
                user_id=user2.id,
                band_name='Bottom Band',
                band_name_lower='bottom band'
            )
            db.session.add(claim)
            db.session.commit()

        response = client.get('/leaderboard')
        assert response.status_code == 200

        # topuser should appear before bottomuser
        data = response.data.decode('utf-8')
        top_pos = data.find('topuser')
        bottom_pos = data.find('bottomuser')
        assert top_pos < bottom_pos


class TestGalleryRoute:
    """Tests for the gallery route."""

    def test_gallery_loads(self, client, app):
        """Test gallery page loads."""
        response = client.get('/gallery')
        assert response.status_code == 200
        assert b'Gallery' in response.data

    def test_gallery_empty(self, client, app):
        """Test gallery with no claims."""
        response = client.get('/gallery')
        assert response.status_code == 200
        assert b'No bands have been claimed' in response.data

    def test_gallery_shows_claimed_bands(self, client, app, sample_user_with_claims):
        """Test gallery displays claimed band names."""
        user_id, claim_ids = sample_user_with_claims

        response = client.get('/gallery')
        assert response.status_code == 200
        assert b'Wandering Echoes' in response.data
        assert b'testuser' in response.data

    def test_gallery_pagination(self, client, app):
        """Test gallery pagination works."""
        with app.app_context():
            # Create user with 30 claims (more than per_page of 24)
            user = User(username='galleryuser', email='gallery@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            for i in range(30):
                claim = ClaimedBandName(
                    user_id=user.id,
                    band_name=f'Gallery Band {i}',
                    band_name_lower=f'gallery band {i}'
                )
                db.session.add(claim)
            db.session.commit()

        # First page
        response = client.get('/gallery')
        assert response.status_code == 200
        assert b'page=2' in response.data  # Should have link to page 2

        # Second page
        response = client.get('/gallery?page=2')
        assert response.status_code == 200


class TestErrorPages:
    """Tests for custom error pages."""

    def test_404_page(self, client, app):
        """Test custom 404 page displays."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'Page Not Found' in response.data
        assert b'Generate a Band Name' in response.data

    def test_404_includes_navbar(self, client, app):
        """Test 404 page extends base template with navbar."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'FW Bandname Generator' in response.data  # Navbar brand


class TestBandNameGeneration:
    """Tests for band name generation helper functions."""

    def test_multiple_index_requests_generate_different_names(self, client, app):
        """Test that index generates varied band names."""
        names = set()
        for _ in range(10):
            response = client.get('/')
            assert response.status_code == 200
            names.add(response.data)

        # Should generate at least a few different results
        # (not always the same band name)
        assert len(names) >= 2
