import pandas as pd
import uuid
from app.core.database import get_db
from fastapi import UploadFile, Depends
from io import StringIO
from sqlalchemy.orm import Session

class StandingsService:
    def __init__(self, db: Session):
        self.db = db

    async def process_csv(self, file: UploadFile):
        """Reads the CSV, processes data, and calls necessary services."""
        df = pd.read_csv(StringIO(await file.read()))
        return df


