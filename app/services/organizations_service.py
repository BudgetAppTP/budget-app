import uuid
from app.extensions import db
from app.models import Organization
from app.utils.types import OrganizationType


def find_or_create_organization(data: dict):
    """Find an organization by name/ICO or create a new one."""
    name = data.get("name")
    ico = data.get("ico")
    address = data.get("streetName")
    municipality = data.get("municipality")

    # Пробуем найти по ICO или по имени
    org = (
        db.session.query(Organization)
        .filter(Organization.name == name)
        .first()
    )

    if org:
        return org

    # Если не нашли — создаём новую
    new_org = Organization(
        name=name,
        type=OrganizationType.MERCHANT,
        address=f"{address}, {municipality}" if address else municipality,
        extra_metadata=data
    )

    db.session.add(new_org)
    db.session.flush()  # получить ID без коммита
    return new_org
