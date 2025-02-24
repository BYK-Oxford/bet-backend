from fastapi import APIRouter, UploadFile, File
from app.standings.services.standing_upload_service import StandingsService
from fastapi import Depends
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/upload-standings-csv/")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)  # Session managed by FastAPIY
):
    """Upload CSV and delegate processing to the service layer."""
    standing_upload_service = StandingsService(db)  # Dependency injection
    return await standing_upload_service.process_csv(file)
