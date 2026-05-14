from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from pyzbar.pyzbar import decode, ZBarSymbol
import re
import cv2
import numpy as np

from app.services.errors import BadRequestError
from app.services.responses import OkResult


class QrService:
    EKASA_PATTERN = r"O-[0-9A-Za-z]{20,}"
    MAX_FILE_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

    def _rotate_variants(self, image):
        return [
            ("rot_0", image),
            ("rot_90", image.rotate(90, expand=True)),
            ("rot_180", image.rotate(180, expand=True)),
            ("rot_270", image.rotate(270, expand=True)),
        ]

    def _match_ekasa(self, text):
        if not text:
            return None
        match = re.search(self.EKASA_PATTERN, text)
        return match.group(0) if match else None

    def _extract_with_pyzbar(self, image):
        try:
            codes = decode(image, symbols=[ZBarSymbol.QRCODE])
        except Exception:
            return None

        for code in codes:
            try:
                qr_data = code.data.decode("utf-8")
            except Exception:
                continue

            receipt_id = self._match_ekasa(qr_data)
            if receipt_id:
                return receipt_id

        return None

    def _extract_with_opencv(self, image):
        try:
            arr = np.array(image)
            if len(arr.shape) == 2:
                img = arr
            else:
                img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

            detector = cv2.QRCodeDetector()
            data, points, _ = detector.detectAndDecode(img)

            receipt_id = self._match_ekasa(data)
            if receipt_id:
                return receipt_id
        except Exception:
            pass

        return None

    def _extract_from_image(self, image):
        receipt_id = self._extract_with_pyzbar(image)
        if receipt_id:
            return receipt_id

        return self._extract_with_opencv(image)

    def extract_ekasa_id(self, file_stream):
        try:
            image = Image.open(file_stream)
            image.load()
        except Exception:
            return None, "Invalid image file"

        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        gray = ImageOps.grayscale(image)
        attempts = [
            ("original", image),
            ("gray", gray),
            ("auto", ImageOps.autocontrast(gray)),
            ("bright2", ImageEnhance.Brightness(gray).enhance(2.0)),
            ("bright3", ImageEnhance.Brightness(gray).enhance(3.0)),
            ("x2", gray.resize((gray.width * 2, gray.height * 2))),
            ("x3", gray.resize((gray.width * 3, gray.height * 3))),
        ]

        for label, variant in attempts:
            for rot_label, rotated in self._rotate_variants(variant):
                receipt_id = self._extract_from_image(rotated)
                if receipt_id:
                    return receipt_id, None

        return None, "QR code not found or does not contain a valid eKasa receipt ID"

    def extract_receipt_id_from_upload(self, uploaded_file):
        if uploaded_file is None:
            raise BadRequestError("Missing image file")

        if not uploaded_file.filename:
            raise BadRequestError("Invalid image file")

        uploaded_file.seek(0, 2)
        size = uploaded_file.tell()
        uploaded_file.seek(0)
        if size > self.MAX_FILE_SIZE:
            raise BadRequestError("File too large. Maximum size is 5MB.")

        filename_lower = uploaded_file.filename.lower()
        if not any(filename_lower.endswith(ext) for ext in self.ALLOWED_EXTENSIONS):
            raise BadRequestError("Invalid file type. Please upload an image.")

        receipt_id, error = self.extract_ekasa_id(uploaded_file.stream)
        if error:
            raise BadRequestError(error)

        if not receipt_id or len(receipt_id) < 10:
            raise BadRequestError("Invalid receipt ID extracted")

        return OkResult({"receiptId": receipt_id})
