"""
Database models for the Finnegans Wake Band Name Generator

Models:
- User: User accounts with OAuth and email/password authentication
- ClaimedBandName: Band names claimed by users (trading card system)
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User model supporting OAuth (Google, GitHub) and email/password authentication.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Email/password authentication
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)

    # OAuth authentication
    oauth_provider = db.Column(
        db.String(50), nullable=True
    )  # 'google', 'github', or None
    oauth_id = db.Column(db.String(255), nullable=True)

    # User profile
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships (will be added in Day 5)
    # claimed_bands = db.relationship('ClaimedBandName', backref='user',
    #                                lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def can_claim(self):
        """Check if user can claim more band names (max 5)"""
        # Will be implemented in Day 5 when ClaimedBandName relationship exists
        # return self.claimed_bands.count() < 5
        return True  # Placeholder for now

    def __repr__(self):
        return f"<User {self.username}>"
