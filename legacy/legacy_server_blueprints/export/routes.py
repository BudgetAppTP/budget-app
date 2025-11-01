from io import BytesIO
from flask import current_app, request, send_file
from . import bp

def _services():
    return current_app.extensions["services"]

@bp.get("/csv")
def csv():
    month = request.args.get("month") or None
    data, name = _services().export.export_csv(month)
    return send_file(BytesIO(data), mimetype="text/csv", as_attachment=True, download_name=name)

@bp.get("/pdf")
def pdf():
    month = request.args.get("month") or None
    data, name = _services().export.export_pdf(month)
    return send_file(BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=name)
