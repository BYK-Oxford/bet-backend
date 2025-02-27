from sqlalchemy.orm import Session
from app.new_odds.models.new_odds_model import NewOdds
from app.teams.services.team_service import TeamService
from app.core.utils import generate_custom_id

class NewOddsService:
    def __init__(self, db: Session):
        self.db = db
        self.team_service = TeamService(db)

    def create_new_odds(self, odds_data: dict):
        """Create or update new odds data in the database."""
        
        # Get or create teams using the team service
        home_team = self.team_service.get_or_create_team(odds_data.get("home_team"))
        away_team = self.team_service.get_or_create_team(odds_data.get("away_team"))
        
        # Check if odds already exist for this match (based on new_odds_id)
        existing_odds = self.db.query(NewOdds).filter_by(new_odds_id=odds_data['new_odds_id']).first()
        if existing_odds:
            return existing_odds  # Prevent duplicate odds

        new_id = generate_custom_id(self.db, NewOdds, "NO", "new_odds_id")  # Generate a custom ID

        # Create a new NewOdds instance with the provided data and team foreign keys
        new_odds = NewOdds(
            new_odds_id=new_id,
            date=odds_data.get("date"),
            time=odds_data.get("time"),
            home_team_id=home_team.team_id,  # Foreign key to Team model
            away_team_id=away_team.team_id,  # Foreign key to Team model
            home_odds=odds_data.get("home_odds"),
            draw_odds=odds_data.get("draw_odds"),
            away_odds=odds_data.get("away_odds")
        )

        # Add the new odds to the session and commit the transaction
        self.db.add(new_odds)
        self.db.commit()
        self.db.refresh(new_odds)
        
        return new_odds
