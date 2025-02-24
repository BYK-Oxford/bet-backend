from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Match(Base):
    __tablename__ = "matches"

    match_id = Column(String, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    league_id = Column(String, ForeignKey("leagues.league_id"))
    season_id = Column(String, ForeignKey("seasons.season_id"))
    home_team_id = Column(String, ForeignKey("teams.team_id"))
    away_team_id = Column(String, ForeignKey("teams.team_id"))
    referee_id = Column(String, ForeignKey("referees.ref_id"))

    league = relationship("League", back_populates="matches")
    season = relationship("Season", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    referee = relationship("Referee", back_populates="matches")
    betting_odds = relationship("BettingOdds", back_populates="match")
    statistics = relationship("MatchStatistics", back_populates="match")
