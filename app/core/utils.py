from sqlalchemy.orm import Session
from sqlalchemy import func

def generate_custom_id(db: Session, model, prefix: str, id_field: str):
    """
    Generate a human-readable unique ID with a prefix using COUNT instead of ORDER BY.
    
    :param db: SQLAlchemy session
    :param model: SQLAlchemy model class
    :param prefix: String prefix for the ID (e.g., "C" for country, "T" for team)
    :param id_field: Field name storing the custom ID
    :return: Generated custom ID (e.g., "C1", "C9999", "C10000", "T1", "T10000")
    """
    # Get the current count of rows in the table
    row_count = db.query(func.count()).select_from(model).scalar()

    # Generate the next ID based on count (avoiding ORDER BY performance hit)
    new_id = row_count + 1
    new_id_str = f"{prefix}{new_id}"

    # Ensure uniqueness by checking if the ID already exists (rare case)
    while db.query(model).filter(getattr(model, id_field) == new_id_str).first():
        new_id += 1
        new_id_str = f"{prefix}{new_id}"

    return new_id_str
