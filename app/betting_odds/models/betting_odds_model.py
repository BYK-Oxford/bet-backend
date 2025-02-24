from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class BettingOdds(Base):
    __tablename__ = "betting_odds"

    betting_oddds_id = Column(String, primary_key=True, index=True)
    match_id = Column(String, ForeignKey("matches.match_id"), nullable=False)
  

    # Full-time result odds
    B365H = Column(Float, nullable=True)  # Bet365 Home Win
    B365D = Column(Float, nullable=True)  # Bet365 Draw
    B365A = Column(Float, nullable=True)  # Bet365 Away Win
    BWH = Column(Float, nullable=True)    # Betway Home Win
    BWD = Column(Float, nullable=True)    # Betway Draw
    BWA = Column(Float, nullable=True)    # Betway Away Win
    BFH = Column(Float, nullable=True)    # Betfair Home Win
    BFD = Column(Float, nullable=True)    # Betfair Draw
    BFA = Column(Float, nullable=True)    # Betfair Away Win
    PSH = Column(Float, nullable=True)    # Pinnacle Home Win
    PSD = Column(Float, nullable=True)    # Pinnacle Draw
    PSA = Column(Float, nullable=True)    # Pinnacle Away Win
    WHH = Column(Float, nullable=True)    # William Hill Home Win
    WHD = Column(Float, nullable=True)    # William Hill Draw
    WHA = Column(Float, nullable=True)    # William Hill Away Win
    MaxH = Column(Float, nullable=True)   # Maximum Home Win odds
    MaxD = Column(Float, nullable=True)   # Maximum Draw odds
    MaxA = Column(Float, nullable=True)   # Maximum Away Win odds
    AvgH = Column(Float, nullable=True)   # Average Home Win odds
    AvgD = Column(Float, nullable=True)   # Average Draw odds
    AvgA = Column(Float, nullable=True)   # Average Away Win odds

    # Over/Under 2.5 Goals odds
    B365_over_2_5 = Column(Float, nullable=True)  # Bet365 Over 2.5 Goals
    B365_under_2_5 = Column(Float, nullable=True) # Bet365 Under 2.5 Goals
    P_over_2_5 = Column(Float, nullable=True)     # Pinnacle Over 2.5 Goals
    P_under_2_5 = Column(Float, nullable=True)    # Pinnacle Under 2.5 Goals
    Max_over_2_5 = Column(Float, nullable=True)   # Maximum Over 2.5 Goals odds
    Max_under_2_5 = Column(Float, nullable=True)  # Maximum Under 2.5 Goals odds
    Avg_over_2_5 = Column(Float, nullable=True)   # Average Over 2.5 Goals odds
    Avg_under_2_5 = Column(Float, nullable=True)  # Average Under 2.5 Goals odds

    # Asian Handicap odds
    AHh = Column(Float, nullable=True)       # Asian Handicap line
    B365AHH = Column(Float, nullable=True)   # Bet365 Asian Handicap Home
    B365AHA = Column(Float, nullable=True)   # Bet365 Asian Handicap Away
    PAHH = Column(Float, nullable=True)      # Pinnacle Asian Handicap Home
    PAHA = Column(Float, nullable=True)      # Pinnacle Asian Handicap Away
    MaxAHH = Column(Float, nullable=True)    # Maximum Asian Handicap Home odds
    MaxAHA = Column(Float, nullable=True)    # Maximum Asian Handicap Away odds
    AvgAHH = Column(Float, nullable=True)    # Average Asian Handicap Home odds
    AvgAHA = Column(Float, nullable=True)    # Average Asian Handicap Away odds

    # Match relationship
    match = relationship("Match", back_populates="betting_odds")
