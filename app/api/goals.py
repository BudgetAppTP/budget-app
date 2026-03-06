import uuid

from flask import request

from app.api import bp
from app.api.auth_context import get_mock_user_id
from app.services.errors import BadRequestError
from app.services import goals_service

@bp.get("/goals", strict_slashes=False)
def api_goals_list():
    user_id = get_mock_user_id()

    fund_id = request.args.get("savings_fund_id")
    fund_uuid = None
    if fund_id:
        try:
            fund_uuid = uuid.UUID(fund_id)
        except ValueError:
            raise BadRequestError("Invalid savings_fund_id format")

    result = goals_service.list_goals(user_id, fund_uuid)
    return result.to_flask_response()


@bp.post("/goals", strict_slashes=False)
def api_goals_create():
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = goals_service.create_goal(user_id, payload_in)
    return result.to_flask_response()


@bp.patch("/goals/<uuid:goal_id>", strict_slashes=False)
def api_goals_update(goal_id: uuid.UUID):
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = goals_service.update_goal_target(user_id, goal_id, payload_in)
    return result.to_flask_response()


@bp.post("/goals/<uuid:goal_id>/allocate", strict_slashes=False)
def api_goals_allocate(goal_id: uuid.UUID):
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = goals_service.adjust_goal_allocation(user_id, goal_id, payload_in.get("delta_amount"))
    return result.to_flask_response()


@bp.post("/goals/<uuid:goal_id>/complete", strict_slashes=False)
def api_goals_complete(goal_id: uuid.UUID):
    user_id = get_mock_user_id()
    result = goals_service.complete_goal(user_id, goal_id)
    return result.to_flask_response()


@bp.post("/goals/<uuid:goal_id>/reopen", strict_slashes=False)
def api_goals_reopen(goal_id: uuid.UUID):
    user_id = get_mock_user_id()
    result = goals_service.reopen_goal(user_id, goal_id)
    return result.to_flask_response()


@bp.delete("/goals/<uuid:goal_id>", strict_slashes=False)
def api_goals_delete(goal_id: uuid.UUID):
    user_id = get_mock_user_id()
    result = goals_service.delete_goal(user_id, goal_id)
    return result.to_flask_response()
