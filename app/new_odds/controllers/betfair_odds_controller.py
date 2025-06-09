from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.new_odds.services.betfair_service import get_betfair_odds
import asyncio

router = APIRouter()

@router.post("/betfair-odds/")
async def get_new_betfair_odds(db: Session = Depends(get_db)):
    """Trigger getting new betfair odds"""
    print(f"🔵 Getting new odds from BetFair")
    
    # Run get_betfair_odds() in a separate thread (non-blocking)
    await asyncio.to_thread(get_betfair_odds)

    return {"message": "Triggered fetching Betfair odds"}
