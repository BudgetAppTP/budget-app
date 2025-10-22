from flask import jsonify
from . import bp

@bp.route("/", methods=["GET"])
def get_receipts():
    # Constant demo data for receipts
    demo_data = [
        {
            "receipt_id": 1,
            "user_id": 12,
            "seller_id": 3,
            "name": "Lidl - potraviny",
            "uid": "A1B2C3",
            "total": 45.20,
            "date": "2025-10-02"
        },
        {
            "receipt_id": 2,
            "user_id": 12,
            "seller_id": 5,
            "name": "Shell - tankovanie",
            "uid": "B7Z8K1",
            "total": 60.00,
            "date": "2025-10-05"
        }
    ]
    return jsonify(demo_data)
