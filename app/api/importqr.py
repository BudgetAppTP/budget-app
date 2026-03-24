"""
Import QR / eKasa API

Paths:
  - POST /api/import-qr/extract-id
"""

from flask import request
from app.api import bp, make_response
import time
from functools import wraps
from app.services.qr_service import QrService

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
                return make_response(None, f"Rate limit exceeded. Try again later.", 429)
            
            # Add current request
            if key not in rate_limit_store:
                rate_limit_store[key] = []
            rate_limit_store[key].append(now)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

qr_service = QrService()

@bp.post("/import-qr/extract-id", strict_slashes=False)
@rate_limit(limit=10, per=60)
def api_importqr_extract_id():
    """
    POST /api/import-qr/extract-id
    Accept an image file, decode the QR code, and return the extracted eKasa receipt ID.
    """
    # Validate file presence
    if "image" not in request.files:
        return make_response(None, "Missing image file", 400)

    file = request.files["image"]
    
    # Validate filename
    if file.filename == "":
        return make_response(None, "Invalid image file", 400)
    
    # Validate file size (max 5MB)
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > 5 * 1024 * 1024:
        return make_response(None, "File too large. Maximum size is 5MB.", 400)
    
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
        return make_response(None, "Invalid file type. Please upload an image.", 400)

    receipt_id, error = qr_service.extract_ekasa_id(file.stream)
    if error:
        return make_response(None, error, 400)
    
    # Validate extracted ID format
    if not receipt_id or len(receipt_id) < 10:
        return make_response(None, "Invalid receipt ID extracted", 400)

    return make_response({"receiptId": receipt_id})