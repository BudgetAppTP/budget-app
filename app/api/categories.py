from . import bp
from flask import jsonify, request
from app.api import bp, make_response

from app.services import categories_service
# GET /api/categories → list all categories
@bp.get("/categories", strict_slashes=False)
def api_categories_list():
    data, status = categories_service.get_all_categories()
    return make_response(data, None, status)

# POST /api/categories → create a new category
@bp.post("/categories", strict_slashes=False)
def create_category():
    data = request.get_json(force=True)
    response, status = categories_service.create_category(data)
    return make_response(response, None, status)

# PUT /api/categories/<id> → update a specific category
@bp.put("/categories/<uuid:category_id>", strict_slashes=False)
def update_income(category_id):
    data = request.get_json()
    if not data:
        return make_response(None,{"code": "bad_request", "message": "Missing JSON body"},400)

    response, status = categories_service.update_income(category_id, data)
    return make_response(response, None, status)

# DELETE /api/categories/<id> → delete a specific category
@bp.delete("/categories/<uuid:category_id>", strict_slashes=False)
def delete_category(category_id):
     response,status =  categories_service.delete_category(category_id)
     return make_response(response, None, status)