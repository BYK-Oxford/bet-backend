import pandas as pd
from io import StringIO
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.standings.models.standings_model import Standing
from app.standings.services.standing_service import StandingService


class StandingsService:
    def __init__(self, db: Session):
        self.db = db
        self.standing_service = StandingService(db)

    async def process_csv(self, file: UploadFile):
        """Reads the CSV, processes data, and calls necessary services."""
        try:
            # Extract league name and season year from filename
            filename = file.filename.replace('.csv', '')
            parts = filename.split('_')

            # Assume last two numeric parts are the season years
            season_year = None
            if len(parts) >= 2 and parts[-2].isdigit() and parts[-1].isdigit():
                season_year = f"{parts[-2]}/{parts[-1]}"
                league_parts = parts[:-2]  # Everything except the last two parts
            else:
                league_parts = parts  # Fallback: treat whole filename as league name

            # Keep digits in league name (like 'Ligue 1', 'Bundesliga 2')
            league_name = ' '.join(word.capitalize() for word in league_parts)
            # Read CSV
            contents = await file.read()
            df = pd.read_csv(StringIO(contents.decode("utf-8")))

            # Rename columns to match expected format
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            with self.db.begin():  # Ensures rollback on error
                for _, row in df.iterrows():
                    standings_data = {
                        "league": league_name,
                        "season": season_year,
                        "team": row["team"],
                        "position": row["position"],
                        "played": row["played"],
                        "wins": row["wins"],
                        "draws": row["draws"],
                        "losses": row["losses"],
                        "goals_for": row["goals_for"],
                        "goals_against": row["goals_against"],
                        "goal_difference": row["goal_difference"],
                        "points": row["points"]
                    }

                    # Call StandingService to handle DB logic
                    self.standing_service.create_standing(standings_data)

            return {"message": "Standings CSV uploaded and processed successfully"}

        except Exception as e:
            self.db.rollback()
            return {"error": f"Failed to process standings CSV: {str(e)}"}


