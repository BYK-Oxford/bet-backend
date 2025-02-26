from sqlalchemy.orm import Session

def generate_custom_id(db: Session, model, prefix: str, id_field: str):
    """
    Generate a human-readable unique ID with a prefix.

    :param db: SQLAlchemy session
    :param model: SQLAlchemy model class
    :param prefix: String prefix for the ID (e.g., "C" for country, "T" for team)
    :param id_field: Field name storing the custom ID
    :return: Generated custom ID (e.g., "C1", "C9999", "C10000", "T1", "T10000")
    """
    latest_entry = db.query(model).order_by(getattr(model, id_field).desc()).first()

    if latest_entry:
        last_id = getattr(latest_entry, id_field)[1:]  # Remove prefix (e.g., "C1234" -> "1234")
        if last_id.isdigit():
            new_id = int(last_id) + 1
        else:
            new_id = 1
    else:
        new_id = 1

    return f"{prefix}{new_id}"
