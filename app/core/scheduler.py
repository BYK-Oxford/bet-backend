import logging
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.live_data.services.live_game_date_service import LiveGameDataService
from app.core.database import SessionLocal
from multiprocessing import Process
import httpx

logger = logging.getLogger(__name__)

base_url = "https://api.betgenieuk.com"
headers = {"Content-Type": "application/json"}


def fetch_betfair_odds():
    """Fetch Betfair odds in a separate process to avoid blocking"""
    from app.core.database import SessionLocal
    from app.new_odds.services.betfair_service import BetfairService

    db = SessionLocal()
    try:
        service = BetfairService(db)
        service.display_filtered_competitions_and_markets()
    except Exception as e:
        logger.error(f"❌ Error in fetch_betfair_odds: {e}")
    finally:
        db.close()


def fetch_league_scraper():
    """Run league table scraper in a separate process"""
    import asyncio

    async def task():
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url}/current-league/scrape-current-league/",
                json={"scraper_name": "thefishy"},
                headers=headers
            )
            logger.info(f"📨 League scraper status: {resp.status_code}")

    asyncio.run(task())


def calculate_odds():
    """Run odds calculation in a separate process"""
    import asyncio

    async def task():
        async with httpx.AsyncClient(timeout=httpx.Timeout(480.0)) as client:
            resp = await client.post(f"{base_url}/odds-calculation/calculate-ratios/", headers=headers)
            logger.info(f"📨 Odds calculation status: {resp.status_code}")

    asyncio.run(task())


def live_game_update():
    """Heavy live game update job"""
    db = SessionLocal()
    service = LiveGameDataService(db=db)
    try:
        service.check_and_update_live_games()
    except Exception as e:
        logger.error(f"❌ Error in live_game_update: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()

    # Step 1: Betfair Odds at 4:00 AM
    @scheduler.scheduled_job(CronTrigger(hour=4, minute=0))
    def step1_job():
        logger.info("🔁 Running Step 1: Betfair Odds")
        p = Process(target=fetch_betfair_odds)
        try:
            p.start()
            p.join()
        except Exception as e:
            logger.error(f"❌ Error in step1job betfair odds getting process: {e}")
        finally:
            if p.is_alive():
                p.terminate()
                p.join()  
                logger.warning("⚠  betfair odds Process terminated forcefully")

    # Step 2: League table scraper at 4:15 AM
    @scheduler.scheduled_job(CronTrigger(hour=4, minute=15))
    def step2_job():
        logger.info("🔁 Running Step 2: League table scraper")
        p = Process(target=fetch_league_scraper)
        try:
            p.start()
            p.join()
        except Exception as e:
            logger.error(f"❌ Error in step2_job fishy table process: {e}")
        finally:
            if p.is_alive():
                p.terminate()
                p.join()  
                logger.warning("⚠ fishy table Process terminated forcefully")

    # Step 3: Odds calculation at 4:30 AM
    @scheduler.scheduled_job(CronTrigger(hour=4, minute=30))
    def step3_job():
        logger.info("🔁 Running Step 3: Odds calculation")
        p = Process(target=calculate_odds)
        try:
            p.start()
            p.join()
        except Exception as e:
            logger.error(f"❌ Error in step3_job calculate  process: {e}")
        finally:
            if p.is_alive():
                p.terminate()
                p.join()  
                logger.warning("⚠ step3_job calculate Process terminated forcefully")


    # Test print job every 6 minutes
    @scheduler.scheduled_job(IntervalTrigger(minutes=6))
    def scheduled_test_print():
        logger.info("-------------------------")
        logger.info("!!!! This is testing and printing scheduler !!!!")
        logger.info("-------------------------")

    # Live game update every 6 minutes (heavy)
    @scheduler.scheduled_job(IntervalTrigger(minutes=6))
    def scheduled_live_update():
        logger.info("🔁 Running scheduled check_and_update_live_games()")
        p = Process(target=live_game_update)
        try:
            p.start()
            p.join()  # wait for process to finish
        except Exception as e:
            logger.error(f"❌ Error in scheduled_live_update process: {e}")
        finally:
            if p.is_alive():
                p.terminate()
                p.join()
                logger.warning("⚠ live_game_update Process terminated forcefully")

    scheduler.start()
    logger.info("✅ Scheduler started with live update + scraper jobs")
