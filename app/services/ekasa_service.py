import requests


EKASA_URL = "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/find"


def fetch_receipt_data(receipt_id: str):
    """
    Call eKasa API to get receipt details by receiptId.
    """
    try:
        response = requests.post(EKASA_URL, json={"receiptId": receipt_id}, timeout=10)
        if response.status_code != 200:
            return {"error": f"eKasa API returned {response.status_code}"}

        data = response.json()
        if data.get("returnValue") != 0:
            return {"error": "Invalid receiptId or not found"}

        return data

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to eKasa API: {str(e)}"}