from sqlalchemy.orm import Session
from app.betting_odds.models import BettingOdds
from app.matches.models import Match
from app.core.utils import generate_custom_id

class BettingOddsService:
    def __init__(self, db: Session):
        self.db = db

    def create_betting_odds(self, odds_data: dict):
        """Create or update betting odds for a match."""
        match = self.db.query(Match).filter(Match.match_id == odds_data["match_id"]).first()

        if not match:
            raise ValueError(f"Match ID {odds_data['match_id']} does not exist.")
        # Generate a structured ID 
        new_id = generate_custom_id(self.db, BettingOdds, "BO", "betting_oddds_id")

        odds = BettingOdds(
            betting_oddds_id=new_id,
            match_id=match.match_id,

            # Full-time result odds
            B365H=odds_data.get("B365H"),
            B365D=odds_data.get("B365D"),
            B365A=odds_data.get("B365A"),
            BWH=odds_data.get("BWH"),
            BWD=odds_data.get("BWD"),
            BWA=odds_data.get("BWA"),
            BFH=odds_data.get("BFH"),
            BFD=odds_data.get("BFD"),
            BFA=odds_data.get("BFA"),
            PSH=odds_data.get("PSH"),
            PSD=odds_data.get("PSD"),
            PSA=odds_data.get("PSA"),
            WHH=odds_data.get("WHH"),
            WHD=odds_data.get("WHD"),
            WHA=odds_data.get("WHA"),
            MaxH=odds_data.get("MaxH"),
            MaxD=odds_data.get("MaxD"),
            MaxA=odds_data.get("MaxA"),
            AvgH=odds_data.get("AvgH"),
            AvgD=odds_data.get("AvgD"),
            AvgA=odds_data.get("AvgA"),

            # Over/Under 2.5 Goals odds
            B365_over_2_5=odds_data.get("B365_over_2_5"),
            B365_under_2_5=odds_data.get("B365_under_2_5"),
            P_over_2_5=odds_data.get("P_over_2_5"),
            P_under_2_5=odds_data.get("P_under_2_5"),
            Max_over_2_5=odds_data.get("Max_over_2_5"),
            Max_under_2_5=odds_data.get("Max_under_2_5"),
            Avg_over_2_5=odds_data.get("Avg_over_2_5"),
            Avg_under_2_5=odds_data.get("Avg_under_2_5"),

            # Asian Handicap odds
            AHh=odds_data.get("AHh"),
            B365AHH=odds_data.get("B365AHH"),
            B365AHA=odds_data.get("B365AHA"),
            PAHH=odds_data.get("PAHH"),
            PAHA=odds_data.get("PAHA"),
            MaxAHH=odds_data.get("MaxAHH"),
            MaxAHA=odds_data.get("MaxAHA"),
            AvgAHH=odds_data.get("AvgAHH"),
            AvgAHA=odds_data.get("AvgAHA"),
        )

        self.db.add(odds)
        self.db.commit()
        self.db.refresh(odds)
        return odds
