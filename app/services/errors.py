from flask import jsonify


class ServiceError(Exception):
    status_code = 500
    default_message = "Internal server error"
    code = "internal_server_error"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message or self.default_message)
        self.code = code or self.code
        if status_code is not None:
            self.status_code = status_code

    def to_flask_response(self):
        return jsonify({
            "data": None,
            "error": {
                "code": self.code or str(self.status_code),
                "message": str(self)
            }
        }), self.status_code


class BadRequestError(ServiceError):
    status_code = 400
    default_message = "Bad request"
    code = "bad_request"


class NotFoundError(ServiceError):
    status_code = 404
    default_message = "Not found"
    code = "not_found"


class ConflictError(ServiceError):
    status_code = 409
    default_message = "Conflict"
    code = "conflict"


class RateLimitExceededError(ServiceError):
    status_code = 429
    default_message = "Rate limit exceeded. Try again later."
    code = "rate_limit_exceeded"
