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

def start_scheduler():
    scheduler = BackgroundScheduler()
    base_url = "https://api.betgenieuk.com"
    headers = {"Content-Type": "application/json"}

    # Step 1: Betfair Odds at 4:00 AM
    @scheduler.scheduled_job(CronTrigger(hour=4, minute=0))
    def step1_job():
        logger.info("🔁 Running Step 1: Betfair Odds")
        async def task():
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{base_url}/betfair-odds/betfair-odds/", headers=headers)
                logger.info(f"📨 Step 1: betfair-odds - {resp.status_code}")
        asyncio.run(task())

    # Step 2: League table scraper at 4:15 AM
    @scheduler.scheduled_job(CronTrigger(hour=4, minute=15))
    def step2_job():
        logger.info("🔁 Running Step 2: League table scraper")
        async def task():
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{base_url}/current-league/scrape-current-league/",
                    json={"scraper_name": "thefishy"},
                    headers=headers
                )
                logger.info(f"📨 Step 2: scrape-current-league - {resp.status_code}")
        asyncio.run(task())

    # Step 3: Odds calculation at 4:30 AM
    @scheduler.scheduled_job(CronTrigger(hour=4, minute=30))
    def step3_job():
        logger.info("🔁 Running Step 3: Odds calculation")
        async def task():
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{base_url}/odds-calculation/calculate-ratios/", headers=headers)
                logger.info(f"📨 Step 3: calculate-ratios - {resp.status_code}")
        asyncio.run(task())


     # 🔁 Job 3: Test print job every 5 minutes (for testing scheduler)
    @scheduler.scheduled_job(IntervalTrigger(minutes=6))
    def scheduled_test_print():
        logger.info("-------------------------")
        logger.info("!!!! This is testing and printing scheduler !!!!")
        logger.info("-------------------------")
        


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
    
    scheduler.start()
    logger.info("✅ Scheduler started with live update + scraper jobs")
