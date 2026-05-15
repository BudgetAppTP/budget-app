"""
Goals API

Paths:
  - GET    /api/funds/{fund_id}/goals
  - POST   /api/funds/{fund_id}/goals
  - PATCH  /api/goals/{goal_id}
  - PUT    /api/goals/{goal_id}
  - DELETE /api/goals/{goal_id}
  - PATCH  /api/goals/{goal_id}/status
  - PATCH  /api/goals/{goal_id}/amount

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  Goal:
    {
      "id": uuid,
      "user_id": uuid,
      "savings_fund_id": uuid,
      "target_amount": float,
      "current_amount": float,
      "is_completed": bool
    }

  GoalStatus:
    {"id": uuid, "is_completed": bool}

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""
import uuid

from flask import g

from app.api import bp
from app.api.request_parsing import parse_json_object_body
from app.services import goals_service


@bp.get("/funds/<uuid:fund_id>/goals", strict_slashes=False)
def api_goals_list_by_fund(fund_id: uuid.UUID):
    """
    Get goals by fund.

    Responses:
      200: {"data": [Goal], "error": null}
      404: see module errors
    """
    user_id = g.current_user.id
    result = goals_service.list_goals_by_fund(user_id, fund_id)
    return result.to_flask_response()


@bp.post("/funds/<uuid:fund_id>/goals", strict_slashes=False)
def api_goals_create(fund_id: uuid.UUID):
    """
    Create goal.

    Request:
      {
        "title": str,
        "description": str | null,
        "target_amount": float
      }

    Responses:
      201: {"data": Goal, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = g.current_user.id
    payload_in = parse_json_object_body()
    result = goals_service.create_goal(user_id, fund_id, payload_in)
    return result.to_flask_response()


@bp.patch("/goals/<uuid:goal_id>", strict_slashes=False)
@bp.put("/goals/<uuid:goal_id>", strict_slashes=False)
def api_goals_update(goal_id: uuid.UUID):
    """
    Update goal basic fields. Status is not updated here.

    Request:
      {
        "title": str,
        "description": str | null,
        "target_amount": float
      }

    Responses:
      200: {"data": Goal, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = g.current_user.id
    payload_in = parse_json_object_body()
    result = goals_service.update_goal(user_id, goal_id, payload_in)
    return result.to_flask_response()


@bp.delete("/goals/<uuid:goal_id>", strict_slashes=False)
def api_goals_delete(goal_id: uuid.UUID):
    """
    Delete goal.

    Responses:
      200: {"data": {"success": true}, "error": null}
      404: see module errors
    """
    user_id = g.current_user.id
    result = goals_service.delete_goal(user_id, goal_id)
    return result.to_flask_response()


@bp.patch("/goals/<uuid:goal_id>/status", strict_slashes=False)
def api_goals_toggle_status(goal_id: uuid.UUID):
    """
    Toggle goal status.

    Request:
      {"is_completed": bool}

    Responses:
      200: {"data": {"id": uuid, "is_completed": bool}, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = g.current_user.id
    payload_in = parse_json_object_body()

    result = goals_service.update_goal_status(user_id, goal_id, payload_in)
    return result.to_flask_response()


@bp.patch("/goals/<uuid:goal_id>/amount", strict_slashes=False)
def api_goals_adjust_amount(goal_id: uuid.UUID):
    """
    Adjust goal current amount.

    Request:
      {"delta_amount": float}

    Responses:
      200: {"data": Goal, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = g.current_user.id
    payload_in = parse_json_object_body()
    if "delta_amount" not in payload_in:
        from app.services.errors import BadRequestError
        raise BadRequestError("Missing delta_amount")

    result = goals_service.adjust_goal_amount(
        user_id,
        goal_id,
        payload_in.get("delta_amount"),
    )
    return result.to_flask_response()
