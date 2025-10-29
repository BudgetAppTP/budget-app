from datetime import datetime

class EkasaClientStub:
    def validate(self, opd: str):
        if not opd or len(opd) < 8:
            return {"valid": False, "reason": "invalid"}
        return {"valid": True, "opd": opd, "issuer": "TERNO", "place": "Hálova", "issued_at": datetime.utcnow().isoformat() + "Z"}
