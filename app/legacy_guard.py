from flask import request, jsonify

def register_legacy_guard(app):
    @app.before_request
    def _block_legacy_paths():
        p = request.path or ""
        if not p.startswith("/api"):
            return jsonify({"data": None, "error": {"code": "gone", "message": "HTML routes were removed"}}), 410
