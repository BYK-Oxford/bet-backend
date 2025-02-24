from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Referee(Base):
    __tablename__ = "referees"

    ref_id = Column(String, primary_key=True, index=True)
    ref_name = Column(String, unique=True, nullable=False)

    matches = relationship("Match", back_populates="referee")
