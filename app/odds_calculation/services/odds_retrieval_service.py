from sqlalchemy.orm import Session
from app.odds_calculation.models.odds_calculation_model import OddsCalculation

class OddsRetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_calculated_odds(self):
        """Retrieve all calculated odds from the database."""
        return self.db.query(OddsCalculation).all()

    def get_calculated_odds_by_match(self, date, time, home_team_id, away_team_id):
        """Retrieve calculated odds for a specific match."""
        return self.db.query(OddsCalculation).filter_by(
            date=date, time=time, home_team_id=home_team_id, away_team_id=away_team_id
        ).first()
