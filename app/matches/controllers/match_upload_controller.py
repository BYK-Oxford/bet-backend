from fastapi import APIRouter, UploadFile, File
from app.matches.services.match_upload_service import UploadService
from fastapi import Depends
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/upload-matches-csv/")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)  # Session managed by FastAPIY
):
    """Upload CSV and delegate processing to the service layer."""
    upload_service = UploadService(db)  # Dependency injection
    return await upload_service.process_csv(file)
