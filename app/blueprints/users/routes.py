from flask import request, jsonify
from . import bp
from app.services import users_service

@bp.route("/", methods=["GET"])
def get_users():
    users = users_service.get_all_users()
    return jsonify(users), 200


@bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    response, status = users_service.create_user(data)
    return jsonify(response), status
