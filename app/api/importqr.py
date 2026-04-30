"""
Import QR / eKasa API

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  ExtractReceiptIdResponse:
    {
      "receiptId": str
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  401: {"data": null, "error": {"code": "unauthenticated", "message": str}}
  429: {"data": null, "error": {"code": "rate_limit_exceeded", "message": str}}
"""

import time
from functools import wraps

from flask import current_app, request

from app.api import bp
from app.services.errors import RateLimitExceededError

# Rate limiting dictionary (in production, use Redis or similar)
rate_limit_store = {}


def rate_limit(limit=10, per=60):
    """Simple rate limiter: limit requests per IP per time period"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr
            key = f"{ip}:{f.__name__}"
            now = time.time()
            
            # Clean old entries
            if key in rate_limit_store:
                rate_limit_store[key] = [t for t in rate_limit_store[key] if now - t < per]
            
            # Check rate limit
            if key in rate_limit_store and len(rate_limit_store[key]) >= limit:
                raise RateLimitExceededError()
            
            # Add current request
            if key not in rate_limit_store:
                rate_limit_store[key] = []
            rate_limit_store[key].append(now)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


def _qr_service():
    """Convenience accessor for the QR extraction service."""
    return current_app.extensions.get("qr_service")

@bp.post("/import-qr/extract-id", strict_slashes=False)
@rate_limit(limit=10, per=60)
def api_importqr_extract_id():
    """
    Extract an eKasa receipt ID from an uploaded QR image.

    Request:
      multipart/form-data with file field:
        image: binary

    Responses:
      200: {"data": ExtractReceiptIdResponse, "error": null}
      400: see module errors
      401: see module errors
      429: see module errors
    """
    result = _qr_service().extract_receipt_id_from_upload(request.files.get("image"))
    return result.to_flask_response()
