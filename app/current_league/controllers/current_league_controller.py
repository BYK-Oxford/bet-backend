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

@router.post("/scrape-current-league/")
async def scrape_current_league(scraper_name: str = "thefishy", db: Session = Depends(get_db)):
    """Trigger scraping for current league standings."""
    urls = load_urls(scraper_name)  # Load the URLs from the JSON file
    scraper_manager = ScraperManager(scraper_name, db)  # Initialize ScraperManager
    
    for url in urls:
        scraper_manager.run_scraper(url)  # Start scraping for each URL
    
    return {"message": f"Scraping started for {scraper_name}"}
