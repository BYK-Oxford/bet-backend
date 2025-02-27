# main.py
import json
from scraper_manager import ScraperManager

def load_urls():
    with open('league_standing_url.json', 'r') as file:
        data = json.load(file)
    return data.get("thefishy", [])

    # with open('odds_urls.json', 'r') as file:
    #     data = json.load(file)
    # return data.get("oddsportal", [])

def main():
    urls = load_urls()  # Load URLs from the JSON file
    
    #scraper_manager = ScraperManager(scraper_name='oddsportal')  # Specify scraper to run
    scraper_manager = ScraperManager(scraper_name='thefishy')  # Specify scraper to run
    
    for url in urls:
        scraper_manager.run_scraper(url)

if __name__ == '__main__':
    main()
