from sqlalchemy.orm import Session
from app.leagues.models import League
from app.country.services.country_service import CountryService  # Assuming you have this
from app.core.utils import generate_custom_id

class LeagueService:
    LEAGUE_NAME_MAPPING = {
        'E0': 'English Premier League',
        'E1': 'English Championship',
        'SC0': 'Scottish Premiership',
        'SC1': 'Scottish Championship',
        'T1': 'Turkish Super League',
        'F1': 'French Ligue 1',
        'I1': 'Italian Serie A',
        'I2': 'Italian Serie B',
        'SP1': 'Spanish La Liga',
        'SP2': 'Spanish Segunda',
        'D1': 'German Bundesliga',
        'D2': 'German Bundesliga 2',
        # Add more mappings as needed
    }
     
    def __init__(self, db: Session):
        self.db = db
        self.country_service = CountryService(db)  # Ensure we can resolve the country

    def get_or_create_league(self, league_name: str):
        '''Retrieve a league by name or code, or create a new one if it doesn't exist.'''
        # First try to find by full name
        league = self.db.query(League).filter(League.league_name == league_name).first()
        
        if not league:
            # If not found, check if it's a league code (E0, E1, etc.)
            league = self.db.query(League).filter(League.league_code == league_name).first()
            
            # If still not found, check if the full name exists in our mapping values
            if not league:
                # Find the code if this is a full name
                for code, mapped_name in self.LEAGUE_NAME_MAPPING.items():
                    if mapped_name == league_name:
                        league = self.db.query(League).filter(League.league_code == code).first()
                        break

        if not league:
            # Get the full league name from the mapping if it's a code, otherwise use the name as is
            full_league_name = self.LEAGUE_NAME_MAPPING.get(league_name, league_name)
            
            # If we got a full name, try to find its corresponding code
            league_code = league_name  # Default to the input
            if league_name not in self.LEAGUE_NAME_MAPPING:
                # If we got a full name, find its code
                for code, mapped_name in self.LEAGUE_NAME_MAPPING.items():
                    if mapped_name == league_name:
                        league_code = code
                        break

            # Create country using the league code (E0, SC0, etc.)
            country = self.country_service.get_or_create_country(league_code)
            
            # Generate a structured ID like C1, C2, C10000
            new_id = generate_custom_id(self.db, League, 'L', 'league_id')

            league = League(
                league_id=new_id,
                league_code=league_code,
                league_name=full_league_name,
                country_id=country.country_id
            )
            self.db.add(league)
            self.db.commit()
            self.db.refresh(league)

        return league
