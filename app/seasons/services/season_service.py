from sqlalchemy.orm import Session
from app.seasons.models import Season
import uuid
from datetime import datetime

class SeasonService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_season(self, season_year: str):
        """Retrieve a season by year or create a new one."""
        # Check if season_year is already in correct format (YYYY/YYYY)
        if '/' in season_year:
            formatted_season = season_year
        else:
            formatted_season = self.determine_season(season_year)
        
        season = self.db.query(Season).filter(Season.season_year == formatted_season).first()
        
        if not season:
            season = Season(
                season_id=str(uuid.uuid4()),
                season_year=formatted_season
            )
            self.db.add(season)
            self.db.commit()
            self.db.refresh(season)

        return season
    
    def determine_season(self, date_str: str) -> str:
        """Determines the football season based on a given match date (DD/MM/YYYY)."""
        match_date = datetime.strptime(date_str, "%d/%m/%Y")
        
        year = match_date.year
        month = match_date.month

        # If match is in January-July, it's part of the previous year's season
        if month <= 7:
            season = f"{year-1}/{year}"
        else:
            season = f"{year}/{year+1}"

        return season
