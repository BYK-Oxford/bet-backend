from sqlalchemy.orm import Session
from app.referee.models import Referee
import uuid

class RefereeService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_referee(self, ref_name: str):
        """Retrieve a referee or create a new one."""
        referee = self.db.query(Referee).filter(Referee.ref_name == ref_name).first()
        
        if not referee:
            referee = Referee(ref_id=str(uuid.uuid4()), ref_name=ref_name)
            self.db.add(referee)
            self.db.commit()
            self.db.refresh(referee)

        return referee
