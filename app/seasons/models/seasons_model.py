from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Season(Base): 
    __tablename__ = "seasons"

    season_id = Column(String, primary_key=True, index=True)
    season_year = Column(String, unique=True, nullable=False)

    matches = relationship("Match", back_populates="season")
    standings = relationship("Standing", back_populates="season")