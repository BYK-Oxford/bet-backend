from sqlalchemy.orm import Session
from app.leagues.models import League
from app.country.services.country_service import CountryService  # Assuming you have this
import uuid

class LeagueService:
    def __init__(self, db: Session):
        self.db = db
        self.country_service = CountryService(db)  # Ensure we can resolve the country

    def get_or_create_league(self, league_name: str):
        """Retrieve a league by name, or create a new one if it doesn't exist."""
        league = self.db.query(League).filter(League.league_name == league_name).first()

        if not league:
            # Get or create country_id from country_name
            country = self.country_service.get_or_create_country(league_name)

            # Generate a UUID for league_id
            league = League(
                league_id=str(uuid.uuid4()),  # Generate unique league_id
                league_code=league_name,
                league_name=league_name,
                country_id=country.country_id  # Assign resolved country_id
            )
            self.db.add(league)
            self.db.commit()
            self.db.refresh(league)

        return league
