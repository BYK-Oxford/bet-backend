from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.odds_calculation.services.odds_calculation_service import OddsCalculationService
from app.new_odds.services.new_odds_service import NewOddsService
from datetime import datetime

router = APIRouter()

@router.post("/calculate-ratios/")
async def calculate_ratios(db: Session = Depends(get_db)):
    """
    Fetches upcoming matches, calculates win, draw, and loss ratios, and returns JSON response.
    """
    try:
        # Initialize services
        odds_service = OddsCalculationService(db)
        new_odds_service = NewOddsService(db)

        # Get future matches
        current_time = datetime.now()
        new_matches = new_odds_service.get_upcoming_matches(current_time)

        if not new_matches:
            return {"message": "No upcoming matches found for ratio calculation."}

        # Perform ratio calculations
        calculated_ratios_list = await odds_service.calculate_ratios_for_matches(new_matches)

        return {"calculated_ratios": calculated_ratios_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))