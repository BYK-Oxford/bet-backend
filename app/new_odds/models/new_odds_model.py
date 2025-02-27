from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Time
from sqlalchemy.orm import relationship
from app.core.database import Base

class NewOdds(Base):
    __tablename__ = "new_odds"

    new_odds_id = Column(String, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    time = Column(Time, nullable=False)

    home_team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    away_team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    
    home_odds = Column(Float)
    draw_odds = Column(Float)
    away_odds = Column(Float)
    
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
