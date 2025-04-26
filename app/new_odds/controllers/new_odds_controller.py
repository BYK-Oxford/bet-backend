from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
    
    urls = load_urls(scraper_name)  # Load the URLs from the JSON file
    print(f"🟠 Loaded {len(urls)} URLs for {scraper_name}")
    
    for idx, url in enumerate(urls):
        print(f"🟣 Preparing to scrape URL {idx+1}/{len(urls)}: {url}")
        
        # 🛠 Create a new ScraperManager for each URL
        scraper_manager = ScraperManager(scraper_name, db, url)
        
        print(f"🟡 Scraping URL {idx+1}/{len(urls)}: {url}")
        await scraper_manager.run_scraper()
        print(f"✅ Scraping Complete +++ {idx+1}/{len(urls)}: {url}")
        
    print(f"✅ Scraping completed for: {scraper_name}")
    
    return {"message": f"Scraping completed for {scraper_name}"}

