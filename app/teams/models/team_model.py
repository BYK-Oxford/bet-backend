from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Team(Base):
    __tablename__ = "teams"

    team_id = Column(String, primary_key=True, index=True)
    team_name = Column(String, unique=True, nullable=False)
    league_id = Column(String, ForeignKey("leagues.league_id"))
    country_id = Column(String, ForeignKey("countries.country_id"))

    league = relationship("League", back_populates="teams")
    country = relationship("Country", back_populates="teams")
    home_matches = relationship("Match", foreign_keys="[Match.home_team_id]", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="[Match.away_team_id]", back_populates="away_team")

    home_odds = relationship("NewOdds", foreign_keys="[NewOdds.home_team_id]", back_populates="home_team")
    away_odds = relationship("NewOdds", foreign_keys="[NewOdds.away_team_id]", back_populates="away_team")




    # Define reverse relationship for TeamAlias
    aliases = relationship("TeamAlias", back_populates="team")

    # Define reverse relationship for Standing
    standings = relationship("Standing", back_populates="team")
    current_league = relationship("CurrentLeague", back_populates="team")
