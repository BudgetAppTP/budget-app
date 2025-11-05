from flask import request, jsonify

def register_legacy_guard(app):
    static_prefix = app.static_url_path or "/static"
    swagger_url = app.config.get("SWAGGER_URL", "/docs") or "/docs"

    allow_prefixes = ("/api", static_prefix, swagger_url)

    @app.before_request
    def _block_legacy_paths():
        # Всегда пропускаем раздачу статики напрямую
        if request.endpoint == "static":
            return None

        p = (request.path or "")
        # Нормализуем, чтобы /foo и /foo/ обрабатывались одинаково
        if p != "/":
            p = p.rstrip("/")

        for pref in allow_prefixes:
            if p.startswith(pref):
                return None

        return jsonify({
            "data": None,
            "error": {"code": "gone", "message": "HTML routes were removed"}
        }), 410
