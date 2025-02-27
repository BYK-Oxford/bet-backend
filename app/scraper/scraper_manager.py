from oddsportal.oddsportal_scraper.oddsportal_scraper import get_page_content_selenium, parse_match_data
from fishy.fishy_scraper.fishy_scraper import get_fishy_page_content_selenium, parse_fishy_league_standing_data
from utils import save_to_csv, save_league_table_to_csv
import re

class ScraperManager:
    def __init__(self, scraper_name):
        self.scraper_name = scraper_name
    
    def run_scraper(self, url):
        if self.scraper_name == 'oddsportal':
            return self._run_oddsportal_scraper(url)
        elif self.scraper_name == 'thefishy':
            return self._run_fishy_scraper(url)
        else:
            raise ValueError("Unsupported scraper name")
    
    def _run_oddsportal_scraper(self, url):
        page_content = get_page_content_selenium(url)
        match_data = parse_match_data(page_content)
        
        # Generate a dynamic filename based on the URL (e.g., using the league name)
        filename = self._generate_filename_from_url(url)
        
        save_to_csv(match_data, scraper_name="oddsportal", filename=filename)
    

        
    def _run_fishy_scraper(self, url):
        page_content = get_fishy_page_content_selenium(url)
        match_data = parse_fishy_league_standing_data(page_content)
        
        # Generate a dynamic filename based on the URL (e.g., using the league name)
        filename = self._generate_filename_from_url(url)
        
        save_league_table_to_csv(match_data, scraper_name="fishy", filename=filename)


    def _generate_filename_from_url(self, url):
        season_mapping = {
            "21": "2023_2024",
            "20": "2022_2023",
            "19": "2021_2022",
            "18": "2020_2021",
            "17": "2019_2020",
        }
        
        table_mapping = {
            "1": "english_premier_league",
            "2": "english_championship",
            "10": "scottish_premier_league",
            "11": "scottish_championship",
        }

        
        if self.scraper_name == 'thefishy':
            match = re.search(r'table=(\d+)&season=(\d+)', url)
            if match:
                table, season = match.groups()
                league = table_mapping.get(table, f"unknown_league_{table}")
                season_years = season_mapping.get(season, f"unknown_season_{season}")
                return f"{league}_{season_years}.csv"
            return "unknown_fishy_data.csv"
    
        elif self.scraper_name == 'oddsportal':
            # Extract the country and league name from the URL
            match = re.search(r'football/([^/]+)/([^/]+)/', url)
            if match:
                country, league = match.groups()
                # Clean and format the filename
                country = country.replace('-', '_')
                league = league.replace('-', '_')
                return f"{country}_{league}_matches.csv"
        
        # Default case for unknown scrapers
        return "unknown_league_matches.csv"
    
  
