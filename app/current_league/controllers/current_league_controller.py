from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import json
import asyncio
from app.core.database import SessionLocal
from app.scraper.scraper_manager import ScraperManager

router = APIRouter()

# Function to load URLs for scraping
def load_urls(scraper_name):
    if scraper_name == "oddsportal":
        with open('app/scraper/odds_urls.json', 'r') as file:
            data = json.load(file)
        return data.get("oddsportal", [])
    elif scraper_name == "thefishy":
        with open('app/scraper/league_standing_url.json', 'r') as file:
            data = json.load(file)
        return data.get("thefishy", [])
    else:
        return []

@router.post("/scrape-current-league/")
async def scrape_current_league(scraper_name: str = "thefishy"):
    """Trigger scraping for current league standings."""
    print(f"🔵 Starting scraping for: {scraper_name}")
    
    urls = load_urls(scraper_name)
    print(f"🟠 Loaded {len(urls)} URLs for {scraper_name}")

    async def background_scrape():
        # Create a fresh DB session for the background task
        db: Session = SessionLocal()
        try:
            for idx, url in enumerate(urls):
                print(f"🟣 Scraping URL {idx+1}/{len(urls)}: {url}")
                scraper_manager = ScraperManager(scraper_name, db)
                await scraper_manager.run_scraper(url)
                print(f"✅ Finished {idx+1}/{len(urls)}: {url}")
            print(f"✅ Scraping completed for {scraper_name}")
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        finally:
            db.close()  # Always close the DB session

    asyncio.create_task(background_scrape())

    return {"message": f"Scraping started for {scraper_name}"}
    
    