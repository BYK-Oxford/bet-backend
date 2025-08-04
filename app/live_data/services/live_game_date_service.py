from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.live_data.models.live_game_data import LiveGameData  # your model import path
from app.odds_calculation.models.odds_calculation_model import OddsCalculation  # if needed for validation

class LiveGameDataService:
    def __init__(self, db: Session):
        self.db = db

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

            # Suppose you have a ScraperService class with method scrape_live_game(scrape_url) -> dict
            from app.scraper_service import ScraperService  # Adjust import path as needed

            # Get existing live game data (to get scrape_url)
            live_data = self.get_live_game_data(odds_calculation_id)
            if not live_data:
                raise ValueError(f"No live game data found for odds_calculation_id {odds_calculation_id}")

            if not live_data.scrape_url:
                raise ValueError(f"No scrape_url set for odds_calculation_id {odds_calculation_id}")

            # Initialize scraper
            scraper = ScraperService()

            # Fetch scraped data from scraper service
            scraped_data = scraper.scrape_live_game(live_data.scrape_url)

            # Update the live game data in DB using your existing method
            updated_live_data = self.create_live_game_data(
                odds_calculation_id=odds_calculation_id,
                is_live=True,
                scrape_url=live_data.scrape_url,
                live_home_score=scraped_data.get("live_home_score"),
                live_away_score=scraped_data.get("live_away_score"),
                match_time=scraped_data.get("match_time"),
                live_home_odds=scraped_data.get("live_home_odds"),
                live_draw_odds=scraped_data.get("live_draw_odds"),
                live_away_odds=scraped_data.get("live_away_odds"),
                shots_on_target_home=scraped_data.get("shots_on_target_home"),
                shots_on_target_away=scraped_data.get("shots_on_target_away"),
                corners_home=scraped_data.get("corners_home"),
                corners_away=scraped_data.get("corners_away"),
            )

            return updated_live_data