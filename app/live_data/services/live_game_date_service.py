from datetime import datetime, timezone
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.live_data.models.live_game_data import LiveGameData  # your model import path
from app.odds_calculation.models.odds_calculation_model import OddsCalculation  # if needed for validation
from app.new_odds.models.new_odds_model import NewOdds  # if needed for validation
from app.teams.models.team_model import Team
from app.scraper.scraper_manager import ScraperManager
from new_odds.services.betfair_service import BetfairService
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

    def trigger_live_data_scrape(self, odds_calculation_id: str):
        """
        Trigger the scraping service/class to fetch live data for given odds_calculation_id.
        This method just calls the external scraper and updates the DB accordingly.
        """
        # Step 1: Fetch the current live game entry
        live_data = self.get_live_game_data(odds_calculation_id)
        if not live_data or not live_data.scrape_url:
            raise ValueError(f"No scrape_url found for odds_calculation_id {odds_calculation_id}")

        # Step 2: Trigger the scraper
        scraper = ScraperManager()
        scraped_data = scraper._run_betfair_scraper(url=live_data.scrape_url)

        if not scraped_data:
            raise ValueError("Scraping failed or returned no data")

        # Update the live game data in DB using your existing method
        updated_live_data = self.create_live_game_data(
            odds_calculation_id=odds_calculation_id,
            is_live=True,
            scrape_url=live_data.scrape_url,
            live_home_score=int(scraped_data.get("Home Score", 0)),
            live_away_score=int(scraped_data.get("Away Score", 0)),
            match_time=scraped_data.get("Time"),
            live_home_odds=None,  # Set if available
            live_draw_odds=None,
            live_away_odds=None,
            shots_on_target_home=int(scraped_data.get("Stats", {}).get("Shots On Target", {}).get("Home", 0)),
            shots_on_target_away=int(scraped_data.get("Stats", {}).get("Shots On Target", {}).get("Away", 0)),
            corners_home=int(scraped_data.get("Stats", {}).get("Corner", {}).get("Home", 0)),
            corners_away=int(scraped_data.get("Stats", {}).get("Corner", {}).get("Away", 0)),
        )

        return updated_live_data
    

    def is_game_live(self, odds_calculation_id: str) -> bool:
        """
        Determine if the given odds_calculation_id corresponds to a currently live game.
        """
        # Step 1: Fetch odds calculation
        odds_calc = self.db.query(OddsCalculation).filter_by(odds_calculation_id=odds_calculation_id).first()
        if not odds_calc:
            raise ValueError(f"OddsCalculation with ID {odds_calculation_id} not found.")

        # Step 2: Fetch home and away team names
        home_team = odds_calc.home_team_id
        away_team = odds_calc.away_team_id
        date = odds_calc.date

        # Step 3: Fetch related NewOdds object and parse full_market_data
        new_odds = self.db.query(NewOdds).filter(
                and_(
                    NewOdds.home_team_id == odds_calc.home_team_id,
                    NewOdds.away_team_id == odds_calc.away_team_id,
                    NewOdds.date == odds_calc.date
                )
            ).first()
        if not new_odds:
            raise ValueError(f"No NewOdds entry found for OddsCalculation ID {odds_calculation_id}.")

        try:
            market_data = json.loads(new_odds.full_market_data)
        except Exception as e:
            raise ValueError("Failed to parse full_market_data JSON.") from e

        event_id = market_data.get("event_id")
        if not event_id:
            raise ValueError("event_id not found in full_market_data.")

        # Step 4: Fetch live games and check for event_id match
        live_games = self.betfafairService.get_live_games_by_league()
        for game in live_games:
            if str(game.get("event_id")) == str(event_id):
                return True

        return False

