from .auth_service import AuthService

def init_auth_service(app):
    """Register the database-backed authentication service on the Flask app."""
    auth_service = AuthService(app)
    app.extensions["auth_service"] = auth_service
    return auth_service
