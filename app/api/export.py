"""
Export API

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Paths:
  - GET /api/export/csv
  - GET /api/export/pdf

Schemas:
  ExportQuery:
    {
      "year": "int | omitted",
      "month": "int | omitted"
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
from app.validators.common_validators import parse_month_year_query_filter


@bp.get("/export/csv", strict_slashes=False)
def api_export_csv():
    """
    Export monthly data as CSV

    Query:
      - year: int | omitted
      - month: int | omitted

    Responses:
      200:
        Content-Type: text/csv
        Body: binary CSV file
      400: see module errors
      404: see module errors
    """
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )
    data, name = export_service.export_csv(g.current_user.id, month_filter=month_filter)
    return send_file(BytesIO(data), mimetype="text/csv", as_attachment=True, download_name=name)


@bp.get("/export/pdf", strict_slashes=False)
def api_export_pdf():
    """
    Export monthly report as PDF

    Query:
      - year: int | omitted
      - month: int | omitted

    Responses:
      200:
        Content-Type: application/pdf
        Body: binary PDF file
      400: see module errors
      404: see module errors
    """
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )
    data, name = export_service.export_pdf(g.current_user.id, month_filter=month_filter)
    return send_file(BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=name)
