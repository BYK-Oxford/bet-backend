from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base

class Standing(Base):
    __tablename__ = "standings"

    standing_id = Column(String, primary_key=True, index=True)
    team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    ranking = Column(Integer, nullable=False)
    league_id = Column(String, ForeignKey("leagues.league_id"), nullable=False)
    season_id = Column(String, ForeignKey("seasons.season_id"), nullable=False)

    team = relationship("Team", back_populates="standings")
    league = relationship("League", back_populates="standings")
    season = relationship("Season", back_populates="standings")
