"""
Export API

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Paths:
  - GET /api/export/csv?month=YYYY-MM
  - GET /api/export/pdf?month=YYYY-MM

Schemas:
  ExportQuery:
    {
      "month": "YYYY-MM | omitted"
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}

Notes:
- These endpoints return files (CSV/PDF) directly. No envelope.
- Content-Disposition: attachment; filename="<derived>"
"""

from io import BytesIO
from flask import g, request, send_file
from app.api import bp
from app.services import export_service


@bp.get("/export/csv", strict_slashes=False)
def api_export_csv():
    """
    Export monthly data as CSV

    Query:
      - month: "YYYY-MM" (optional)

    Responses:
      200:
        Content-Type: text/csv
        Body: binary CSV file
      400: see module errors
      404: see module errors
    """
    month = request.args.get("month") or None
    data, name = export_service.export_csv(g.current_user.id, month)
    return send_file(BytesIO(data), mimetype="text/csv", as_attachment=True, download_name=name)


@bp.get("/export/pdf", strict_slashes=False)
def api_export_pdf():
    """
    Export monthly report as PDF

    Query:
      - month: "YYYY-MM" (optional)

    Responses:
      200:
        Content-Type: application/pdf
        Body: binary PDF file
      400: see module errors
      404: see module errors
    """
    month = request.args.get("month") or None
    data, name = export_service.export_pdf(g.current_user.id, month)
    return send_file(BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=name)
