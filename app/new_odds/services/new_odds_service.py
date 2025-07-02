from sqlalchemy.orm import Session
from app.new_odds.models.new_odds_model import NewOdds
from app.core.utils import generate_custom_id
from app.seasons.services.season_service import SeasonService
from datetime import datetime
from app.leagues.services.league_service import LeagueService
from app.leagues.models.leagues_models import League

class NewOddsService:
    def __init__(self, db: Session):
        self.db = db
        self.season_service = SeasonService(db)
        self.league_service = LeagueService(db)

    def get_upcoming_matches(self, current_time: datetime):
        """Fetches all upcoming matches based on system date and time."""
        return self.db.query(NewOdds).filter(NewOdds.date > current_time.date()).all()

    def _find_matching_league(self, league_code: str) -> League:
        """Find the matching league using league_code."""
        league = self.db.query(League).filter(League.league_code == league_code).first()
        if not league:
            raise ValueError(f"Could not find matching league for code: {league_code}")
        return league

    def create_new_odds(self, odds_data: dict):
        """Create or update new odds data in the database."""            
        # Skip if any of the odds values are '-'
        if (odds_data['home_odds'] == '-' or 
            odds_data['draw_odds'] == '-' or 
            odds_data['away_odds'] == '-'):
            return None
        
        # Convert string date to datetime if it's not already
        if isinstance(odds_data['date'], str):
            try:
                date_obj = datetime.strptime(odds_data['date'], '%d %b %Y')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except ValueError as e:
                raise ValueError(f"Invalid date format: {odds_data['date']}. Expected 'DD MMM YYYY'") from e
        else:
            formatted_date = odds_data['date'].strftime('%d/%m/%Y')
        
        # Get or create season
        season = self.season_service.get_or_create_season(formatted_date)
        
        # Find matching league using league_code
        league = self._find_matching_league(odds_data['league_code'])
        
        # Check if odds already exist for this match
        existing_odds = self.db.query(NewOdds).filter_by(
            home_team_id=odds_data['home_team_id'],
            away_team_id=odds_data['away_team_id'],
            date=odds_data['date'],
            time=odds_data['time']
        ).first()
        
        if existing_odds:
            # Update existing odds with new values
            existing_odds.home_odds = odds_data['home_odds']
            existing_odds.draw_odds = odds_data['draw_odds']
            existing_odds.away_odds = odds_data['away_odds']
            existing_odds.season_id = season.season_id
            existing_odds.league_id = league.league_id
            existing_odds.full_market_data = odds_data['full_market_data']
            self.db.commit()
            self.db.refresh(existing_odds)
            return existing_odds

        # Generate a custom ID for new odds
        new_id = generate_custom_id(self.db, NewOdds, "NO", "new_odds_id")

        # Create a new NewOdds instance with the provided data
        new_odds = NewOdds(
            new_odds_id=new_id,
            date=odds_data['date'],
            time=odds_data['time'],
            home_team_id=odds_data['home_team_id'],
            away_team_id=odds_data['away_team_id'],
            home_odds=odds_data['home_odds'],
            draw_odds=odds_data['draw_odds'],
            away_odds=odds_data['away_odds'],
            season_id=season.season_id,
            league_id=league.league_id,
            full_market_data=odds_data['full_market_data']

        )


        # Add the new odds to the session and commit the transaction
        self.db.add(new_odds)
        self.db.commit()
        self.db.refresh(new_odds)
        
        return new_odds
