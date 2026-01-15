"""
User routes for the Finnegans Wake Band Name Generator.

Handles user dashboard and band name claims management.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import ClaimedBandName


# Create user blueprint
user_bp = Blueprint('user_bp', __name__, url_prefix='/user')


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """Display user's dashboard with their claimed band names"""
    # Get user's claimed bands, most recent first
    claimed_bands = current_user.claimed_bands.order_by(
        ClaimedBandName.claimed_at.desc()
    ).all()

    claim_count = len(claimed_bands)
    max_claims = 5

    return render_template(
        'user/dashboard.html',
        claimed_bands=claimed_bands,
        claim_count=claim_count,
        max_claims=max_claims,
    )
