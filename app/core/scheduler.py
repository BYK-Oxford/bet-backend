import asyncio
import logging
import traceback
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.live_data.services.live_game_date_service import LiveGameDataService
from app.core.database import SessionLocal
import httpx

logger = logging.getLogger(__name__)


async def call_scraper_api():
    base_url = "https://api.betgenieuk.com"
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            # 🔵 Step 1: Betfair Odds
            betfair_response = await client.post(
                f"{base_url}/betfair-odds/betfair-odds/",
                headers=headers
            )
            logger.info(f"📨 Step 1: betfair-odds - {betfair_response.status_code}")
            await asyncio.sleep(5)

            # Step 2: League table scraper
            league_response = await client.post(
                f"{base_url}/current-league/scrape-current-league/",
                json={"scraper_name": "thefishy"},
                headers=headers
            )
            logger.info(f"📨 Step 2: scrape-current-league - {league_response.status_code}")
            await asyncio.sleep(5)

            # Step 3: Odds calculation
            calc_response = await client.post(
                f"{base_url}/odds-calculation/calculate-ratios/",
                headers=headers
            )
            logger.info(f"📨 Step 3: calculate-ratios - {calc_response.status_code}")

        except Exception as e:
            logger.error("❌ Error in scheduled scraping chain", exc_info=True)


def start_scheduler():
    scheduler = BackgroundScheduler()

    # 🔁 Job 1: Live game update
    @scheduler.scheduled_job(IntervalTrigger(minutes=6))
    def scheduled_live_update():
        logger.info("🔁 Running scheduled check_and_update_live_games()")
        db = SessionLocal()
        service = LiveGameDataService(db=db)
        try:
            service.check_and_update_live_games()
        except Exception as e:
            logger.error(f"❌ Error in live update scheduler: {e}")
        finally:
            db.close()

   # 🔁 Job 2: Scraper job (runs Tue & Thu at 1:00 PM)
    @scheduler.scheduled_job(CronTrigger(hour=12, minute=42))
    def scheduled_scraper_call():
        logger.info("🔁 Running scheduled scraper API calls (everyday at 4AM)")
        try:
            asyncio.run(call_scraper_api())
        except Exception as e:
            logger.error(f"❌ Error running scheduled scraper call: {e}", exc_info=True)

    
     # 🔁 Job 3: Test print job every 5 minutes (for testing scheduler)
    @scheduler.scheduled_job(IntervalTrigger(minutes=5))
    def scheduled_test_print():
        logger.info("-------------------------")
        logger.info("!!!! This is testing and printing scheduler !!!!")
        logger.info("-------------------------")
        

    scheduler.start()
    logger.info("✅ Scheduler started with live update + scraper jobs")
