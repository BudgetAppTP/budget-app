"""
Export API

Paths:
  - GET /api/export/csv?month=YYYY-MM
  - GET /api/export/pdf?month=YYYY-MM

Notes:
- These endpoints return files (CSV/PDF) directly. No envelope.
- Content-Disposition: attachment; filename="<derived>"
"""

from io import BytesIO
from flask import current_app, request, send_file
from app.api import bp


def _services():
    return current_app.extensions["services"]


@bp.get("/export/csv", strict_slashes=False)
def api_export_csv():
    """
    GET /api/export/csv?month=YYYY-MM
    Summary: Export monthly data as CSV

    Query:
      - month: "YYYY-MM" (optional)

    Responses:
      200:
        Content-Type: text/csv
        Body: binary CSV file
    """
    month = request.args.get("month") or None
    data, name = _services().export.export_csv(month)
    return send_file(BytesIO(data), mimetype="text/csv", as_attachment=True, download_name=name)


@bp.get("/export/pdf", strict_slashes=False)
def api_export_pdf():
    """
    GET /api/export/pdf?month=YYYY-MM
    Summary: Export monthly report as PDF

    Query:
      - month: "YYYY-MM" (optional)

    Responses:
      200:
        Content-Type: application/pdf
        Body: binary PDF file
    """
    month = request.args.get("month") or None
    data, name = _services().export.export_pdf(month)
    return send_file(BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=name)
