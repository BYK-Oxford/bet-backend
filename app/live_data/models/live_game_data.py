from sqlalchemy import Column, String, ForeignKey, Boolean, Float, Integer, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class LiveGameData(Base):
    __tablename__ = "live_game_data"

    odds_calculation_id = Column(
        String,
        ForeignKey("odds_calculations.odds_calculation_id"),
        primary_key=True,
        index=True
    )

    is_live = Column(Boolean, default=False)
    scrape_url = Column(String, nullable=True)

    # Live Scores
    live_home_score = Column(Integer, nullable=True)
    live_away_score = Column(Integer, nullable=True)
    match_time = Column(String, nullable=True)  # e.g., "45+2", "73", or "HT"

    # Live Odds
    live_home_odds = Column(Float, nullable=True)
    live_draw_odds = Column(Float, nullable=True)
    live_away_odds = Column(Float, nullable=True)

    # Match Stats
    shots_on_target_home = Column(Integer, nullable=True)
    shots_on_target_away = Column(Integer, nullable=True)
    shots_off_target_home = Column(Integer, nullable=True)
    shots_off_target_away = Column(Integer, nullable=True)
    corners_home = Column(Integer, nullable=True)
    corners_away = Column(Integer, nullable=True)

    # Last updated time
    last_updated = Column(DateTime, nullable=True)

    # Relationship to OddsCalculation
    odds_calculation = relationship("OddsCalculation", back_populates="live_data")
