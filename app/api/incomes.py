from flask import request
from app.api import bp, make_response
from app.services import incomes_service

@bp.get("/incomes")
def api_incomes_list():
    data, status = incomes_service.get_all_incomes()
    incomes_list = data.get("incomes", [])
    sort_by = request.args.get("sort", "income_date")
    order = request.args.get("order", "desc")
    reverse = order.lower() == "desc"
    try:
        incomes_list.sort(key=lambda i: i[sort_by], reverse=reverse)
    except Exception:
        pass
    data["incomes"] = incomes_list
    return make_response(data, None, status)

@bp.post("/incomes")
def api_incomes_create():
    payload = request.get_json(force=True) or {}
    response, status = incomes_service.create_income(payload)
    return make_response(response, None, status)

@bp.get("/incomes/<uuid:income_id>")
def api_incomes_get(income_id):
    response, status = incomes_service.get_income_by_id(income_id)
    return make_response(response, None, status)

@bp.put("/incomes/<uuid:income_id>")
def api_incomes_update(income_id):
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = incomes_service.update_income(income_id, payload)
    return make_response(response, None, status)

@bp.delete("/incomes/<uuid:income_id>")
def api_incomes_delete(income_id):
    response, status = incomes_service.delete_income(income_id)
    return make_response(response, None, status)
