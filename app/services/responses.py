from flask import jsonify


class ServiceResult:
    status_code = 200

    def __init__(self, payload=None):
        self.payload = payload

    def to_dict(self):
        return {"data": self.payload, "error": None}

    def to_flask_response(self):
        return jsonify(self.to_dict()), self.status_code


class OkResult(ServiceResult):
    status_code = 200


class CreatedResult(ServiceResult):
    status_code = 201
