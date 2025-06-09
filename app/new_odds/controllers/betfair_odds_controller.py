from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import asyncio
import json

router = APIRouter()


@router.post("/betfair-odds/")
async def get_new_betfair_odds(db: Session = Depends(get_db)):
    """Trigger getting new betfair odds"""
    print(f"🔵Getting new odds from BetFair")
    
    
