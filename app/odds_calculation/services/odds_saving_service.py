from sqlalchemy.orm import Session
from app.odds_calculation.models.odds_calculation_model import OddsCalculation
from datetime import datetime
from app.core.utils import generate_custom_id

class OddsSavingService:
    def __init__(self, db: Session):
        self.db = db

    def save_calculated_odds(self, date: datetime, time: datetime.time, home_team_id: str, away_team_id: str, odds_data: dict, stats_metrics: dict):
        """
        Save the calculated odds to the database. If an entry with the same date, time, home_team_id, and away_team_id exists, update it instead of inserting a new one.
        """
        try:
            existing_entry = self.db.query(OddsCalculation).filter(
                OddsCalculation.date == date,
                OddsCalculation.time == time,
                OddsCalculation.home_team_id == home_team_id,
                OddsCalculation.away_team_id == away_team_id
            ).first()

            if existing_entry:
                existing_entry.calculated_home_odds = odds_data.get("final_home_win_ratio")
                existing_entry.calculated_draw_odds = odds_data.get("final_draw_chance")
                existing_entry.calculated_away_odds = odds_data.get("final_away_win_ratio")
                existing_entry.stats_banded_data = stats_metrics
                self.db.commit()
                self.db.refresh(existing_entry)
                return existing_entry
            
            new_id = generate_custom_id(self.db, OddsCalculation, "OC", "odds_calculation_id")
            print(f"Generated ID: {new_id}")
            
            new_entry = OddsCalculation(
                odds_calculation_id=new_id,
                date=date,
                time=time,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                calculated_home_odds=odds_data.get("final_home_win_ratio"),
                calculated_draw_odds=odds_data.get("final_draw_chance"),
                calculated_away_odds=odds_data.get("final_away_win_ratio"),
                stats_banded_data=stats_metrics
            )
            self.db.add(new_entry)
            self.db.commit()
            self.db.refresh(new_entry)
            return new_entry  # Return new_entry instead of existing_entry
        except Exception as e:
            self.db.rollback()  # rollback to prevent dirty session
            raise e
        
