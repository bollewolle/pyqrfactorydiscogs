"""
Flask application initialization for Discogs Collection to QR Factory CSV Generator
"""

from flask import Flask

def create_app():
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        instance_relative_config=True
    )

    # Configuration
    app.config.from_mapping(
        SECRET_KEY='dev',  # TODO: Change for production!
        PERMANENT_SESSION_LIFETIME=3600,  # 1 hour session timeout
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload size
    )
    
    # Set environment variable for testing mode
    if app.config.get('TESTING', False):
        import os
        os.environ['FLASK_TESTING'] = '1'

    # Register blueprints
    from app import routes

    app.register_blueprint(routes.bp)

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return 'OK', 200

    return app
