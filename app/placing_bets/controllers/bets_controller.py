from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.placing_bets.services.odds_processor_service import OddsProcessorService

router = APIRouter()

@router.get("/v4m-sets/")
def get_v4m_sets(db: Session = Depends(get_db)):
    """
    Retrieve value 4 money sets.
    """
    try:
        odds_processor_service = OddsProcessorService(db)
        v4m_matches = odds_processor_service.find_value_for_money_sets()

        if not v4m_matches:
            return {"message": "No v4m_matches computed found."}

        return {"v4m": v4m_matches}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

