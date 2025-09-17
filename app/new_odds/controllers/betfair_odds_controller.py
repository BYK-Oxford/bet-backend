from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.new_odds.services.betfair_service import BetfairService
import asyncio

router = APIRouter()

@router.post("/betfair-odds/")
async def get_new_betfair_odds():
    """Trigger getting new betfair odds in background"""
    print(f"🔵 Getting new odds from BetFair")

    async def background_task():
        db: Session = SessionLocal()  # create a fresh session for the thread
        try:
            betfair_service = BetfairService(db)
            # Run the blocking method in thread
            await asyncio.to_thread(
                betfair_service.display_filtered_competitions_and_markets
            )
        except Exception as e:
            db.rollback()
            print(f"❌ Error in Betfair background task: {e}")
        finally:
            db.close()  # ensure session is closed

    asyncio.create_task(background_task())

    return {"message": "Triggered fetching Betfair odds"}
