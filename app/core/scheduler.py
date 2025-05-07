from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = BackgroundScheduler()

    # CronTrigger: At 02:30 AM every day
    trigger = CronTrigger(hour=2, minute=30)

    @scheduler.scheduled_job(trigger)
    def scheduled_scrape():
        asyncio.run(call_scraper_api())

    scheduler.start()
    logger.info("✅ Scheduler started")

async def call_scraper_api():
    base_url = "https://bet-backend-1.onrender.com"
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            # 1️⃣ Step 1: Trigger oddsportal scraper
            odds_response = await client.post(
                f"{base_url}/odds/scrape-new-odds/",
                json={"scraper_name": "oddsportal"},
                headers=headers
            )
            logger.info(f"📨 Step 1: scrape-new-odds - {odds_response.status_code}")
            await asyncio.sleep(5)  # 💤 Breathing room (5 seconds)

            # 2️⃣ Step 2: Trigger current league standing scraper
            league_response = await client.post(
                f"{base_url}/current-league/scrape-current-league/",
                json={"scraper_name": "thefishy"},
                headers=headers
            )
            logger.info(f"📨 Step 2: scrape-current-league - {league_response.status_code}")
            await asyncio.sleep(5)  # 💤 Breathing room (5 seconds)

            # 3️⃣ Step 3: Trigger odds calculation
            calc_response = await client.post(
                f"{base_url}/odds-calculation/calculate-ratios/",
                headers=headers
            )
            logger.info(f"📨 Step 3: calculate-ratios - {calc_response.status_code}")

        except Exception as e:
            logger.error(f"❌ Error in scheduled scraping chain: {e}")
