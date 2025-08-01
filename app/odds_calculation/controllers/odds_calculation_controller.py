from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.odds_calculation.services.odds_calculation_service import OddsCalculationService
from app.new_odds.services.new_odds_service import NewOddsService
from app.odds_calculation.services.odds_retrieval_service import OddsRetrievalService
from datetime import datetime

router = APIRouter()

@router.get("/calculated-odds/")
def get_all_calculated_odds(db: Session = Depends(get_db)):
    """
    Retrieve all calculated odds from the database.
    """
    try:
        odds_service = OddsRetrievalService(db)
        calculated_odds = odds_service.get_all_calculated_odds()

        if not calculated_odds:
            return {"message": "No calculated odds found."}

        return {"calculated_odds": calculated_odds}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        print(f"[LOG] Total upcoming matches fetched: {len(new_matches)}")

        if not new_matches:
            return {"message": "No upcoming matches found for ratio calculation."}

        # Perform ratio calculations
        calculated_ratios_list = await odds_service.calculate_ratios_for_matches(new_matches)

        # return {"calculated_ratios": calculated_ratios_list}
        return {"message": "All odds calculations done for upcoming matches  !!!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))