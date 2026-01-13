from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
import os

from app.models import db, User


def create_app(config_name=None):
    """
    Application factory pattern for Flask app.

    Args:
        config_name: Configuration to use (development, production, testing, or None for auto-detect)

    Returns:
        Flask application instance
    """
    # Get the parent directory (project root)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Create Flask app
    app = Flask(
        __name__,
        static_folder=os.path.join(basedir, "static"),
        template_folder="templates",
    )

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    from config import config

    app.config.from_object(config[config_name])

    # Initialize extensions
    Bootstrap(app)
    db.init_app(app)
    migrate = Migrate(app, db, render_as_batch=True)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "main_bp.index"  # Redirect to index if not logged in

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    # Note: Database tables are created via migrations (flask db upgrade)
    # Not using db.create_all() to ensure migrations are the single source of truth

    return app


# Create app instance for development
app = create_app()
