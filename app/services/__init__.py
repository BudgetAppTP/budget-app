from .auth_service import AuthService
from .qr_service import QrService

def init_auth_service(app):
    """Register the database-backed authentication service on the Flask app."""
    auth_service = AuthService(app)
    app.extensions["auth_service"] = auth_service
    return auth_service


def init_qr_service(app):
    """Register the QR extraction service on the Flask app."""
    qr_service = QrService()
    app.extensions["qr_service"] = qr_service
    return qr_service
