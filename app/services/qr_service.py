from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from pyzbar.pyzbar import decode, ZBarSymbol
import re
import cv2
import numpy as np


class QrService:
    EKASA_PATTERN = r"O-[0-9A-Za-z]{20,}"

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
                    print(f"QR found with: {label} + {rot_label}")
                    return receipt_id, None

        return None, "QR code not found or does not contain a valid eKasa receipt ID"


qr_service = QrService()