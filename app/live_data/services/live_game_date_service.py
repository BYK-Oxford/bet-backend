from datetime import datetime, timezone
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.live_data.models.live_game_data import LiveGameData  # your model import path
from app.odds_calculation.models.odds_calculation_model import OddsCalculation  # if needed for validation
from app.new_odds.models.new_odds_model import NewOdds  # if needed for validation
from app.teams.models.team_model import Team
from app.scraper.scraper_manager import ScraperManager
from app.new_odds.services.betfair_service import BetfairService
import json


class LiveGameDataService:
    def __init__(self, db: Session):
        self.db = db
        self.betfafairService = BetfairService(db)

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

    def trigger_live_data_scrape(self, odds_calculation_id: str, scrape_url: str):
        """
        Trigger the scraper using the provided scrape_url and update or create live game data
        using the given odds_calculation_id.
        """
        if not odds_calculation_id or not scrape_url:
            raise ValueError("Both odds_calculation_id and scrape_url must be provided.")

        # Run the scraper
        scraper = ScraperManager()
        scraped_data = scraper._run_betfair_scraper(url=scrape_url)

        if not scraped_data:
            raise ValueError("Scraping failed or returned no data")

        # Check if match time is FT (Full Time)
        match_time = scraped_data.get("Time")
        is_live_status = False if match_time and match_time.strip().upper() == "FT" else True

        # Perform create or update (your create_live_game_data should handle upsert logic)
        self.create_live_game_data(
            odds_calculation_id=odds_calculation_id,
            is_live=is_live_status,
            scrape_url=scrape_url,
            live_home_score=int(scraped_data.get("Home Score", 0)),
            live_away_score=int(scraped_data.get("Away Score", 0)),
            match_time=scraped_data.get("Time"),
            live_home_odds=None,
            live_draw_odds=None,
            live_away_odds=None,
            shots_on_target_home=int(scraped_data.get("Stats", {}).get("Shots On Target", {}).get("Home", 0)),
            shots_on_target_away=int(scraped_data.get("Stats", {}).get("Shots On Target", {}).get("Away", 0)),
            corners_home=int(scraped_data.get("Stats", {}).get("Corner", {}).get("Home", 0)),
            corners_away=int(scraped_data.get("Stats", {}).get("Corner", {}).get("Away", 0)),
        )


    def check_and_update_live_games(self):
        """
        Check all today's games and trigger live data scraping for games that are live.
        """
        today = date.today()

        # Step 1: Fetch all OddsCalculation entries for today
        todays_odds_calculations = self.db.query(OddsCalculation).filter(OddsCalculation.date == today).all()
        if not todays_odds_calculations:
            print("No odds calculations found for today.")
            return

        # Step 2: Get all live games from Betfair
        live_games = self.betfafairService.get_live_games_by_league()
        live_games_dict = {str(game.get("event_id")): game for game in live_games if game.get("event_id")}

        # Step 3: Iterate and check for matches
        for odds_calc in todays_odds_calculations:
            new_odds = self.db.query(NewOdds).filter(
                and_(
                    NewOdds.home_team_id == odds_calc.home_team_id,
                    NewOdds.away_team_id == odds_calc.away_team_id,
                    NewOdds.date == odds_calc.date
                )
            ).first()

            if not new_odds:
                continue

            try:
                market_data = json.loads(new_odds.full_market_data)
                event_id = str(market_data.get("event_id"))
            except Exception:
                continue

            live_game = live_games_dict.get(event_id)
            if live_game:
                standard_url = live_game.get("standard_url")
                try:
                    self.trigger_live_data_scrape(odds_calculation_id=odds_calc.odds_calculation_id, scrape_url=standard_url)
                    print(f"Live data scraped and saved for event_id: {event_id}")
                except Exception as e:
                    print(f"Error scraping live data for event_id {event_id}: {str(e)}")
