from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Time
from sqlalchemy.orm import relationship
from app.core.database import Base

class OddsCalculation(Base):
    __tablename__ = "odds_calculations"

    odds_calculation_id = Column(String, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    time = Column(Time, nullable=False)

    home_team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    away_team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    
    calculated_home_odds = Column(Float)
    calculated_draw_odds = Column(Float)
    calculated_away_odds = Column(Float)
    
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_calculated_odds")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_calculated_odds")
