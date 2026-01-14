"""
OAuth initialization for Google and GitHub authentication

Uses Authlib for OAuth 2.0 implementation.
"""

from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_oauth(app):
    """
    Initialize OAuth with the Flask app and register providers.

    Args:
        app: Flask application instance

    Returns:
        Configured OAuth instance
    """
    oauth.init_app(app)

    # Google OAuth 2.0
    # Uses OpenID Connect discovery for automatic configuration
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    # GitHub OAuth 2.0
    oauth.register(
        name='github',
        client_id=app.config.get('GITHUB_CLIENT_ID'),
        client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )

    return oauth
