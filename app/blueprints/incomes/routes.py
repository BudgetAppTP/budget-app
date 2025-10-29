from flask import jsonify, request
from app.services import incomes_service
from . import bp

# GET /incomes → list all incomes with optional sorting
@bp.route("/", methods=["GET"])
def list_incomes():
    data, status = incomes_service.get_all_incomes()
    incomes_list = data["incomes"]
    sort_by = request.args.get("sort", "income_date")  # default sorting
    order = request.args.get("order", "desc")          # ascending/descending

    reverse = order.lower() == "desc"
    incomes_list.sort(key=lambda i: i[sort_by], reverse=reverse)
    data["incomes"] = incomes_list
    return jsonify(data), status

# POST /incomes → create a new income
@bp.route("/", methods=["POST"])
def create_income():
    data = request.get_json(force=True)
    response, status = incomes_service.create_income(data)
    return jsonify(response), status

# GET /incomes/<id> → get a specific income
@bp.route("/<uuid:income_id>", methods=["GET"])
def get_income(income_id):
    response, status = incomes_service.get_income_by_id(income_id)
    return jsonify(response), status

# PUT /incomes/<id> → update a specific income
@bp.route("/<uuid:income_id>", methods=["PUT"])
def update_income(income_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    response, status = incomes_service.update_income(income_id, data)
    return jsonify(response), status


# DELETE /incomes/<id> → delete a specific income
@bp.route("/<uuid:income_id>", methods=["DELETE"])
def delete_income(income_id):
     response,status =  incomes_service.delete_income(income_id)
     return jsonify(response), status