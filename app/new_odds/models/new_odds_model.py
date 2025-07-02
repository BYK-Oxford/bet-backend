from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Time
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class NewOdds(Base):
    __tablename__ = "new_odds"

    new_odds_id = Column(String, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    time = Column(Time, nullable=False)
    season_id = Column(String, ForeignKey("seasons.season_id"), nullable=False)
    league_id = Column(String, ForeignKey("leagues.league_id"), nullable=False)

    home_team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    away_team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    
    home_odds = Column(Float)
    draw_odds = Column(Float)
    away_odds = Column(Float)

    full_market_data = Column(JSONB, nullable=True)
    
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_odds")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_odds")
    season = relationship("Season", back_populates="odds")
    league = relationship("League", back_populates="new_odds")
