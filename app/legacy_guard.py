from flask import request, jsonify

def register_legacy_guard(app):
    allow_prefixes = ["/api", "/static"]

    swagger_url = app.config.get("SWAGGER_URL", "/api/docs")
    if swagger_url and not swagger_url.startswith("/api"):
        allow_prefixes.append(swagger_url)

    @app.before_request
    def _block_legacy_paths():
        p = (request.path or "")
        if p == "/":
            return None
        for pref in allow_prefixes:
            if p.startswith(pref):
                return None
        return jsonify({"data": None, "error": {"code": "gone", "message": "HTML routes were removed"}}), 410
