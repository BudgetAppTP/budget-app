from PIL import Image
from pyzbar.pyzbar import decode
import re

class QrService:

    EKASA_PATTERN = r"O-[0-9A-Za-z]{20,}"

    def extract_ekasa_id(self, file_stream):
        try:
            image = Image.open(file_stream)
        except Exception:
            return None, "Invalid image file"

        codes = decode(image)

        if not codes:
            return None, "QR code not found"

        qr_data = codes[0].data.decode("utf-8")

        match = re.search(self.EKASA_PATTERN, qr_data)
        if not match:
            return None, "eKasa receipt ID not found"

        return match.group(0), None


qr_service = QrService()