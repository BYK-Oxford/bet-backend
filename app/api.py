from fastapi import APIRouter
from app.matches.controllers.match_upload_controller import router as upload_match_router
from app.standings.controllers.standings_upload_controller import router as upload_standing_router

api_router = APIRouter()

api_router.include_router(upload_match_router, prefix="/match", tags=["match"])
api_router.include_router(upload_standing_router, prefix="/standing", tags=["standing"])
