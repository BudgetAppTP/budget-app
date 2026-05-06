import requests

from app.services.errors import BadRequestError, UpstreamServiceError


EKASA_URL = "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/find"


def fetch_receipt_data(receipt_id: str):
    """
    Call eKasa API to get receipt details by receiptId.
    """
    try:
        response = requests.post(EKASA_URL, json={"receiptId": receipt_id}, timeout=10)
        if response.status_code != 200:
            raise UpstreamServiceError(f"eKasa API returned {response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise UpstreamServiceError("Invalid response returned by eKasa API") from exc

        if data.get("returnValue") != 0:
            raise BadRequestError("Invalid receiptId or not found")

        return data

    except requests.exceptions.RequestException as exc:
        raise UpstreamServiceError(f"Failed to connect to eKasa API: {str(exc)}") from exc
