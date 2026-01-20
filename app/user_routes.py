"""
User routes for the Finnegans Wake Band Name Generator.

Handles user dashboard and band name claims management.
"""

import re

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

from app.models import db, ClaimedBandName


# Load existing bands for real band name checking
BANDSPATH = "static/data/bands.txt"
with open(BANDSPATH, "r") as f:
    existing_bands = {
        line.strip().lower()
        for line in f
        if line.strip() and not re.match(r"^Q\d+$", line.strip())
    }


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


@user_bp.route('/claim', methods=['POST'])
@login_required
def claim_band():
    """Claim a band name for the current user (AJAX endpoint)"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    band_name = data.get('band_name', '').strip()
    if not band_name:
        return jsonify({'error': 'Band name is required'}), 400

    # Check claim limit
    if not current_user.can_claim:
        return jsonify({'error': 'Maximum 5 claims reached'}), 403

    # Normalize for comparison
    normalized = ClaimedBandName.normalize_name(band_name)

    # Check if already claimed by anyone
    existing_claim = ClaimedBandName.query.filter_by(band_name_lower=normalized).first()
    if existing_claim:
        return jsonify({
            'error': f'Already claimed by {existing_claim.user.username}'
        }), 409

    # Check if it's a real band name
    if normalized in existing_bands:
        return jsonify({'error': 'This is a real band name'}), 400

    # Create the claim
    claim = ClaimedBandName(
        user_id=current_user.id,
        band_name=band_name,
        band_name_lower=normalized
    )
    db.session.add(claim)
    db.session.commit()

    return jsonify({
        'success': True,
        'claim_id': claim.id,
        'message': f'Successfully claimed "{band_name}"!'
    }), 201


@user_bp.route('/unclaim/<int:claim_id>', methods=['POST'])
@login_required
def unclaim_band(claim_id):
    """Release a claimed band name"""
    # Find the claim
    claim = ClaimedBandName.query.get_or_404(claim_id)

    # Authorization check: only the owner can unclaim
    if claim.user_id != current_user.id:
        flash('You can only unclaim your own bands.', 'danger')
        return redirect(url_for('user_bp.dashboard'))

    band_name = claim.band_name

    # Delete the claim
    db.session.delete(claim)
    db.session.commit()

    flash(f'Released "{band_name}" back into the wild!', 'success')
    return redirect(url_for('user_bp.dashboard'))
