from flask import jsonify, request
from . import bp

demo_incomes = [
    {"id": 1, "date": "2025-10-01", "description": "Výplata", "amount": 1200.00},
    {"id": 2, "date": "2025-10-05", "description": "Darček od babky", "amount": 200.00},
    {"id": 3, "date": "2025-10-10", "description": "Predaj starého bicykla", "amount": 350.00},
]

demo_expenses = [
    {"id": 1, "date": "2025-10-02", "category": "Jedlo", "amount": 45.20},
    {"id": 2, "date": "2025-10-05", "category": "Doprava", "amount": 14.00},
    {"id": 3, "date": "2025-10-07", "category": "Byvanie", "amount": 865.00},
]


# GET /incomes → list all incomes with optional sorting
@bp.route("/", methods=["GET"])
def list_incomes():
    sort_by = request.args.get("sort_by", "date")
    order = request.args.get("order", "asc")
    reverse = order == "desc"

    sorted_incomes = sorted(
        demo_incomes,
        key=lambda x: float(x["amount"]) if sort_by == "amount" else x["date"],
        reverse=reverse,
    )
    total_amount = sum(i["amount"] for i in sorted_incomes)

    return jsonify({
        "success": True,
        "incomes": sorted_incomes,
        "total_amount": total_amount
    }), 200


# POST /incomes → create a new income
@bp.route("/", methods=["POST"])
def create_income():
    data = request.get_json(force=True)
    if not data or "amount" not in data or "date" not in data or "description" not in data:
        return jsonify({"success": False, "error": "Invalid input data"}), 400

    new_id = demo_incomes[-1]["id"] + 1 if demo_incomes else 1
    new_income = {
        "id": new_id,
        "date": data["date"],
        "description": data["description"],
        "amount": float(data["amount"]),
    }
    demo_incomes.append(new_income)
    return jsonify({"success": True, "income": new_income}), 201

# PUT /incomes/<id> → update a specific income
@bp.route("/<int:item_id>", methods=["PUT"])
def update_income(item_id):
    income = next((i for i in demo_incomes if i["id"] == item_id), None)
    if not income:
        return jsonify({"success": False, "error": "Income not found"}), 404

    data = request.get_json(force=True)
    income["date"] = data.get("date", income["date"])
    income["description"] = data.get("description", income["description"])
    income["amount"] = float(data.get("amount", income["amount"]))
    return jsonify({"success": True, "income": income}), 200


# DELETE /incomes/<id> → delete a specific income
@bp.route("/<int:item_id>", methods=["DELETE"])
def delete_income(item_id):
    income = next((i for i in demo_incomes if i["id"] == item_id), None)
    if not income:
        return jsonify({"success": False, "error": "Income not found"}), 404

    demo_incomes.remove(income)
    return jsonify({"success": True, "incomes": demo_incomes}), 200
