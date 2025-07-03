from fastapi import APIRouter
from app.matches.controllers.match_upload_controller import router as upload_match_router
from app.standings.controllers.standings_upload_controller import router as upload_standing_router
from app.current_league.controllers.current_league_controller import router as current_league_router
from app.new_odds.controllers.new_odds_controller import router as new_odds_router
from app.placing_bets.controllers.bets_controller import router as betting_router
from app.new_odds.controllers.betfair_odds_controller import router as betfair_router
from app.odds_calculation.controllers.odds_calculation_controller import router as odds_calculation_router
from app.match_statistics.controllers.match_statistics_controller import router as match_statistics_router 

api_router = APIRouter()

api_router.include_router(upload_match_router, prefix="/match", tags=["match"])
api_router.include_router(upload_standing_router, prefix="/standing", tags=["standing"])
api_router.include_router(current_league_router, prefix="/current-league", tags=["current-league"])
api_router.include_router(new_odds_router, prefix="/odds", tags=["odds"])
api_router.include_router(betfair_router, prefix="/betfair-odds", tags=["new-betfair-odds"])
api_router.include_router(betting_router, prefix="/betting-router", tags=["new-betting-router"])
api_router.include_router(odds_calculation_router, prefix="/odds-calculation", tags=["odds-calculation"])
api_router.include_router(match_statistics_router, prefix="/match-statistics", tags=["match-statistics"]) 