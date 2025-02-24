from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class MatchStatistics(Base):
    __tablename__ = "match_statistics"

    match_stat_id = Column(String, primary_key=True, index=True)
    match_id = Column(String, ForeignKey("matches.match_id"), nullable=False)

    # Full-Time Goals
    full_time_home_goals = Column(Integer, nullable=False)  # FTHG
    full_time_away_goals = Column(Integer, nullable=False)  # FTAG
    full_time_result = Column(String, nullable=False)  # FTR

    # Half-Time Goals
    half_time_home_goals = Column(Integer, nullable=False)  # HTHG
    half_time_away_goals = Column(Integer, nullable=False)  # HTAG
    half_time_result = Column(String, nullable=False)  # HTR

    # Match Events
    shots_home = Column(Integer, nullable=False)
    shots_away = Column(Integer, nullable=False)
    shots_on_target_home = Column(Integer, nullable=False)
    shots_on_target_away = Column(Integer, nullable=False)
    fouls_home = Column(Integer, nullable=False)
    fouls_away = Column(Integer, nullable=False)
    corners_home = Column(Integer, nullable=False)
    corners_away = Column(Integer, nullable=False)
    yellow_cards_home = Column(Integer, nullable=False)
    yellow_cards_away = Column(Integer, nullable=False)
    red_cards_home = Column(Integer, nullable=False)
    red_cards_away = Column(Integer, nullable=False)

    # Relationship with Match
    match = relationship("Match", back_populates="statistics")
