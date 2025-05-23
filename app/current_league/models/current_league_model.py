from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base

class CurrentLeague(Base):
    __tablename__ = "current_league"

    current_league_id = Column(String, primary_key=True, index=True)
    team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    league_id = Column(String, ForeignKey("leagues.league_id"), nullable=False)
    season_id = Column(String, ForeignKey("seasons.season_id"), nullable=False)

    position = Column(Integer, nullable=False)  # Renamed from ranking
    played = Column(Integer, nullable=False)
    wins = Column(Integer, nullable=False)
    draws = Column(Integer, nullable=False)
    losses = Column(Integer, nullable=False)
    goals_for = Column(Integer, nullable=False)
    goals_against = Column(Integer, nullable=False)
    goal_difference = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)

    team = relationship("Team", back_populates="current_league")
    league = relationship("League", back_populates="current_leagues")
    season = relationship("Season", back_populates="current_leagues")