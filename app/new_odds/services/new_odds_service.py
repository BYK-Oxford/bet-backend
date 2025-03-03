from sqlalchemy.orm import Session
from app.new_odds.models.new_odds_model import NewOdds
from app.core.utils import generate_custom_id

class NewOddsService:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update_odds(self, odds_data: dict):
        """Create or update new odds data in the database."""
        
        # Skip if any of the odds values are '-'
        if odds_data['home_odds'] == '-' or odds_data['draw_odds'] == '-' or odds_data['away_odds'] == '-':
            return None
        
        # Check if odds already exist for this match (same teams, date, and time)
        existing_odds = self.db.query(NewOdds).filter(
            NewOdds.home_team_id == odds_data['home_team_id'],
            NewOdds.away_team_id == odds_data['away_team_id'],
            NewOdds.date == odds_data['date'],
            NewOdds.time == odds_data['time']
        ).first()
        
        if existing_odds:
            # Update existing odds
            existing_odds.home_odds = odds_data['home_odds']
            existing_odds.draw_odds = odds_data['draw_odds']
            existing_odds.away_odds = odds_data['away_odds']
            self.db.commit()
            self.db.refresh(existing_odds)
            return existing_odds

        # If no existing record, generate a custom ID and create a new entry
        new_id = generate_custom_id(self.db, NewOdds, "NO", "new_odds_id")

        new_odds = NewOdds(
            new_odds_id=new_id,
            date=odds_data['date'],
            time=odds_data['time'],
            home_team_id=odds_data['home_team_id'],
            away_team_id=odds_data['away_team_id'],
            home_odds=odds_data['home_odds'],
            draw_odds=odds_data['draw_odds'],
            away_odds=odds_data['away_odds']
        )

        self.db.add(new_odds)
        self.db.commit()
        self.db.refresh(new_odds)
        
        return new_odds
