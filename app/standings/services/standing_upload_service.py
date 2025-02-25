import pandas as pd
import uuid
from io import StringIO
from sqlalchemy.orm import Session
from fastapi import UploadFile, Depends
from app.core.database import get_db
from app.standings.models.standings_model import Standing

class StandingsService:
    def __init__(self, db: Session):
        self.db = db

    async def process_csv(self, file: UploadFile):
        """Reads the CSV, processes data, and calls necessary services."""
        try:
            # Get league name from filename
            filename = file.filename.replace('.csv', '')  # Remove .csv extension
            # Remove year pattern if exists (e.g., _2022_2023)
            league_name = '_'.join(word for word in filename.split('_') 
                                 if not any(c.isdigit() for c in word))
            # Convert to title case with proper spacing
            league_name = ' '.join(word.capitalize() for word in league_name.split('_'))

            # Read CSV
            contents = await file.read()
            df = pd.read_csv(StringIO(contents.decode("utf-8")))
            
            # Rename columns to match expected format
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            for _, row in df.iterrows():
                # Prepare standings data
                standings_data = {
                    "standing_id": str(uuid.uuid4()),
                    "league_name": league_name,
                    "team_name": row["team"], 
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
                
                # Create new standing entry
                standing = Standing(**standings_data)
                self.db.add(standing)
            
            # Commit all changes
            self.db.commit()
            return {"message": "Standings CSV uploaded and processed successfully"}

        except Exception as e:
            self.db.rollback()
            return {"error": f"Failed to process standings CSV: {str(e)}"}


