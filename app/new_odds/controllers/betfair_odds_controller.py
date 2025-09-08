from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.database import get_db
from app.new_odds.services.betfair_service import BetfairService
import asyncio

router = APIRouter()

@router.post("/betfair-odds/")
async def get_new_betfair_odds(db: Session = Depends(get_db)):
    """Trigger getting new betfair odds"""
    print(f"🔵 Getting new odds from BetFair")
    
    betfair_service = BetfairService(db)
    
    # Run in background, don't await (returns immediately)
    asyncio.create_task(asyncio.to_thread(
        betfair_service.display_filtered_competitions_and_markets
    ))
    return {"message": "Triggered fetching Betfair odds"}
