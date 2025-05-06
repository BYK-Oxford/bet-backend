from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import asyncio
import json
from app.core.database import get_db
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

@router.post("/scrape-new-odds/")
async def scrape_new_odds(scraper_name: str = "oddsportal", db: Session = Depends(get_db)):
    """Trigger scraping for new odds."""
    print(f"🔵 Starting scraping for: {scraper_name}")
    
    urls = load_urls(scraper_name)
    total = len(urls)
    print(f"🟠 Loaded {total} URLs for {scraper_name}")
    
    for idx, url in enumerate(urls):
        print(f"🟣 Preparing to scrape URL {idx+1}/{total}: {url}")
        scraper_manager = ScraperManager(scraper_name, db)
        
        try:
            print(f"🟡 Scraping URL {idx+1}/{total}: {url}")
            success = await scraper_manager.run_scraper(url)
            
            if success:
                print(f"✅ Scraping complete: {idx+1}/{total}: {url}")
            else:
                print(f"⚠️ No data scraped or failed: {url}")
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
        
        # Throttle to avoid bans or load issues
        await asyncio.sleep(2.5)
    
    print(f"✅ All scraping done for: {scraper_name}")
    return {"message": f"Scraping completed for {scraper_name}"}
