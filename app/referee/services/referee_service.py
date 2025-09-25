from sqlalchemy.orm import Session
from app.referee.models import Referee
from app.core.utils import generate_custom_id

class RefereeService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_referee(self, ref_name: str):
        """Retrieve a referee or create a new one."""
        try:
            referee = self.db.query(Referee).filter(Referee.ref_name == ref_name).first()
            
            if not referee:
                new_id = generate_custom_id(self.db, Referee, "R", "ref_id")

                referee = Referee(ref_id=new_id, ref_name=ref_name)
                self.db.add(referee)
                self.db.commit()
                self.db.refresh(referee)

            return referee
        except:
            self.db.rollback()
            raise
