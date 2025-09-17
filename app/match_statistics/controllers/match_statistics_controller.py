from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.match_statistics.services.match_statistics_service import MatchStatisticsService

router = APIRouter()


@router.get("/matches/statistics")
def get_all_match_statistics(db: Session = Depends(get_db)):
    """
    Get all match statistics from the match_statistics table.
    """
    try:
        stats_service = MatchStatisticsService(db)
        statistics = stats_service.get_all_match_statistics()

        if not statistics:
            return {"message": "No match statistics found."}

        return {"match_statistics": statistics}

    except Exception as e:#
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/matches/historic/{id}")
def get_historic_matches_by_odds_calculation(id: str, db: Session = Depends(get_db)):
    """
    Get historic matches with teams, league, country, and statistics based on odds calculation ID.
    """
    try:
        stats_service = MatchStatisticsService(db)
        matches = stats_service.get_historic_matches_between_teams(id)

        if not matches:
            return {"message": "No historic match data found for the given odds calculation."}

        return matches

    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))