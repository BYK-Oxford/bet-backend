from datetime import datetime, timezone
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.live_data.models.live_game_data import LiveGameData  # your model import path
from app.live_data.services.sofa_service import SofaScoreService  # your model import path
from app.odds_calculation.models.odds_calculation_model import OddsCalculation  # if needed for validation
from app.new_odds.models.new_odds_model import NewOdds  # if needed for validation
from app.teams.models.team_model import Team
from app.new_odds.services.betfair_service import BetfairService
import json

class LiveGameDataService:
    def __init__(self, db: Session):
        self.db = db
        self.betfafairService = BetfairService(db)
        self.sofa_service = SofaScoreService()
        # Load team aliases from JSON file once
        with open("app/teams/teams_aliases.json", "r") as f:
            self.team_aliases = json.load(f)
        # Create a mapping from lowercased alias to canonical name
        self.alias_to_team = {}
        for canonical, aliases in self.team_aliases.items():
            for alias in aliases:
                self.alias_to_team[alias.strip().lower()] = canonical

    def normalize_team_name(self, name: str) -> str:
        """
        Converts a team name to its canonical version using aliases.
        If no alias found, returns the original name lowercased.
        """
        return self.alias_to_team.get(name.strip().lower(), name.strip().lower())

    def create_live_game_data(
        self,
        odds_calculation_id: str,
        is_live: bool = False,
        scrape_url: str | None = None,
        live_home_score: int | None = None,
        live_away_score: int | None = None,
        match_time: str | None = None,
        live_home_odds: float | None = None,
        live_draw_odds: float | None = None,
        live_away_odds: float | None = None,
        shots_on_target_home: int | None = None,
        shots_on_target_away: int | None = None,
        shots_off_target_home: int | None = None,
        shots_off_target_away: int | None = None,
        corners_home: int | None = None,
        corners_away: int | None = None,
    ) -> LiveGameData:
        # Optional: check if OddsCalculation exists
        odds_calc = self.db.query(OddsCalculation).filter_by(odds_calculation_id=odds_calculation_id).first()
        if not odds_calc:
            raise ValueError(f"OddsCalculation with id {odds_calculation_id} not found")

        # Check if live data already exists for this odds_calculation_id
        live_data = self.db.query(LiveGameData).filter_by(odds_calculation_id=odds_calculation_id).first()
        if live_data:
            # Update existing
            live_data.is_live = is_live
            live_data.scrape_url = scrape_url
            live_data.live_home_score = live_home_score
            live_data.live_away_score = live_away_score
            live_data.match_time = match_time
            live_data.live_home_odds = live_home_odds
            live_data.live_draw_odds = live_draw_odds
            live_data.live_away_odds = live_away_odds
            live_data.shots_on_target_home = shots_on_target_home
            live_data.shots_on_target_away = shots_on_target_away
            live_data.shots_off_target_home = shots_off_target_home
            live_data.shots_off_target_away = shots_off_target_away
            live_data.corners_home = corners_home
            live_data.corners_away = corners_away
            live_data.last_updated = datetime.now(timezone.utc)

        else:
            # Create new row
            live_data = LiveGameData(
                odds_calculation_id=odds_calculation_id,
                is_live=is_live,
                scrape_url=scrape_url,
                live_home_score=live_home_score,
                live_away_score=live_away_score,
                match_time=match_time,
                live_home_odds=live_home_odds,
                live_draw_odds=live_draw_odds,
                live_away_odds=live_away_odds,
                shots_on_target_home=shots_on_target_home,
                shots_on_target_away=shots_on_target_away,
                shots_off_target_home=shots_off_target_home,
                shots_off_target_away=shots_off_target_away,
                corners_home=corners_home,
                corners_away=corners_away,
                last_updated=datetime.now(timezone.utc)
            )
            self.db.add(live_data)

        self.db.commit()
        self.db.refresh(live_data)
        return live_data

 
    def get_live_game_data(self, odds_calculation_id: str) -> LiveGameData | None:
        return self.db.query(LiveGameData).filter_by(odds_calculation_id=odds_calculation_id).first()

    async def check_and_update_live_games(self):
        today = date.today()
        todays_odds_calculations = self.db.query(OddsCalculation).filter(
            OddsCalculation.date == today
        ).all()
        if not todays_odds_calculations:
            print("No odds calculations found for today.")
            return

        # 1️⃣ Get Betfair live games
        betfair_live_games = self.betfafairService.get_live_games_by_league()
        betfair_live_dict = {str(g.get("event_id")): g for g in betfair_live_games if g.get("event_id")}

        # 2️⃣ Get SofaScore live matches
        sofascore_live_matches = self.sofa_service.get_live_matches()

        for odds_calc in todays_odds_calculations:
            new_odds = self.db.query(NewOdds).filter(
                and_(
                    NewOdds.home_team_id == odds_calc.home_team_id,
                    NewOdds.away_team_id == odds_calc.away_team_id,
                    NewOdds.date == odds_calc.date
                )
            ).first()

            if not new_odds:
                print(f"No new odds for odds_calculation_id {odds_calc.odds_calculation_id}")
                continue

            try:
                market_data = json.loads(new_odds.full_market_data)
                event_id = str(market_data.get("event_id"))
            except Exception:
                print(f"Failed to load market data for odds_calculation_id {odds_calc.odds_calculation_id}")
                continue

            # Check if game is live in Betfair
            betfair_game = betfair_live_dict.get(event_id)
            if not betfair_game:
                print(f"No live Betfair match for event_id: {event_id}")
                continue

            # Get Betfair team names
            # Normalize team names using aliases
            betfair_home = self.normalize_team_name(betfair_game.get("home_team", ""))
            betfair_away = self.normalize_team_name(betfair_game.get("away_team", ""))

            # Match with SofaScore
            matched_sofa_game = next(
                (
                    m for m in sofascore_live_matches
                    if self.normalize_team_name(m.get("homeTeam", {}).get("name", "")) == betfair_home
                    and self.normalize_team_name(m.get("awayTeam", {}).get("name", "")) == betfair_away
                ),
                None
            )

            if not matched_sofa_game:
                print(f"No SofaScore match for Betfair game {betfair_home} vs {betfair_away}")
                continue

            # Update DB with SofaScore live stats
            self.create_live_game_data(
                odds_calculation_id=odds_calc.odds_calculation_id,
                is_live=True,
                scrape_url=None,
                live_home_score=matched_sofa_game.get("homeScore", {}).get("current"),
                live_away_score=matched_sofa_game.get("awayScore", {}).get("current"),
                match_time=matched_sofa_game.get("currentMinute"),
                live_home_odds=betfair_game.get("home_odds"),
                live_draw_odds=betfair_game.get("draw_odds"),
                live_away_odds=betfair_game.get("away_odds"),
                shots_on_target_home=matched_sofa_game.get("homeShotsOnTarget"),
                shots_on_target_away=matched_sofa_game.get("awayShotsOnTarget"),
                shots_off_target_home=matched_sofa_game.get("homeShotsOffTarget"),
                shots_off_target_away=matched_sofa_game.get("awayShotsOffTarget"),
                corners_home=matched_sofa_game.get("cornerKicksHome"),
                corners_away=matched_sofa_game.get("cornerKicksAway"),
            )

            print(f"✅ Updated live data for {betfair_home} vs {betfair_away}")
