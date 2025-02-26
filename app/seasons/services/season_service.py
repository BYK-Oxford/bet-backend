from sqlalchemy.orm import Session
from app.seasons.models import Season
from app.core.utils import generate_custom_id
from datetime import datetime

class SeasonService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_season(self, season_input: str):
        """Retrieve a season by match date or create a new one."""
        
        # If input is already in "YYYY/YYYY" format, use it directly
        if '/' in season_input and len(season_input) == 9:
            formatted_season = season_input
        else:
            formatted_season = self.determine_season(season_input)

        season = self.db.query(Season).filter(Season.season_year == formatted_season).first()

        if not season:
            new_id = generate_custom_id(self.db, Season, "S", "season_id")

            season = Season(
                season_id=new_id,
                season_year=formatted_season
            )
            self.db.add(season)
            self.db.commit()
            self.db.refresh(season)

        return season

    def determine_season(self, date_str: str) -> str:
        """Determines the football season based on a given match date (DD/MM/YYYY)."""
        try:
            match_date = datetime.strptime(date_str, "%d/%m/%Y")
            year = match_date.year
            month = match_date.month

            # If match is in January-July, it's part of the previous year's season
            if month <= 7:
                return f"{year-1}/{year}"
            else:
                return f"{year}/{year+1}"

        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected 'DD/MM/YYYY'.")

