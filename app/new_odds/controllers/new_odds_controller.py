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
    urls = load_urls(scraper_name)  # Load the URLs from the JSON file
    scraper_manager = ScraperManager(scraper_name, db)  # Initialize ScraperManager
    
    for url in urls:
        await scraper_manager.run_scraper(url)  # Start scraping for each URL
    
    return {"message": f"Scraping Completed for {scraper_name}"}
