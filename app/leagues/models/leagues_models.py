from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class League(Base):
    __tablename__ = "leagues"

    league_id = Column(String, primary_key=True, index=True)
    league_code = Column(String)
    league_name = Column(String, unique=True, nullable=False)
    country_id = Column(String, ForeignKey("countries.country_id"))

    country = relationship("Country", back_populates="leagues")
    teams = relationship("Team", back_populates="league")
    matches = relationship("Match", back_populates="league")
    standings = relationship("Standing", back_populates="league")
