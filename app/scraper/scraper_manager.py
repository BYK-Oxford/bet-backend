from app.scraper.oddsportal.oddsportal_scraper.oddsportal_scraper import get_page_content_selenium, parse_match_data
from app.scraper.fishy.fishy_scraper import get_fishy_page_content_selenium, parse_fishy_league_standing_data
from app.new_odds.services.new_odds_service import NewOddsService
from app.current_league.services.current_league_service import CurrentLeagueService
from sqlalchemy.orm import Session

class ScraperManager:
    def __init__(self, scraper_name, db: Session):
        self.scraper_name = scraper_name
        self.new_odds_service = NewOddsService(db)
        self.current_league_service = CurrentLeagueService(db)
        
        # Mapping URLs to league codes for OddsPortal
        self.oddsportal_league_mapping = {
            "https://www.oddsportal.com/football/england/premier-league/": "E0",
            "https://www.oddsportal.com/football/england/championship/": "E1",
            "https://www.oddsportal.com/football/scotland/premiership/": "SC0",
            "https://www.oddsportal.com/football/scotland/championship/": "SC1"
        }

        # Mapping URLs to league codes for TheFishy
        self.fishy_league_mapping = {
            "https://thefishy.co.uk/leaguetable.php?table=1": "E0",  # Premier League
            "https://thefishy.co.uk/leaguetable.php?table=2": "E1",  # Championship
            "https://thefishy.co.uk/leaguetable.php?table=10": "SC0", # Scottish Premier League
            "https://thefishy.co.uk/leaguetable.php?table=11": "SC1"  # Scottish Championship
        }
    
    def run_scraper(self, url):
        if self.scraper_name == 'oddsportal':
            return self._run_oddsportal_scraper(url)
        elif self.scraper_name == 'thefishy':
            return self._run_fishy_scraper(url)
        else:
            raise ValueError("Unsupported scraper name")
    
    def _run_oddsportal_scraper(self, url):
        # Get league code from the URL mapping for OddsPortal
        league_code = self.oddsportal_league_mapping.get(url)
        if not league_code:
            raise ValueError(f"Unknown URL for OddsPortal scraper: {url}")
        
        page_content = get_page_content_selenium(url)
        match_data = parse_match_data(page_content)
        
        # Assuming match_data contains the required fields matching NewOdds model
        for match in match_data:
            new_odds_data = {
                'date': match['date'],
                'time': match['time'],
                'home_team_id': match['home_team_id'],
                'away_team_id': match['away_team_id'],
                'home_odds': match['home_odds'],
                'draw_odds': match['draw_odds'],
                'away_odds': match['away_odds'],
                'league_code': league_code  # Adding the league code
            }
            self.new_odds_service.create_new_odds(new_odds_data)
    
    def _run_fishy_scraper(self, url):
        # Get league code from the URL mapping for TheFishy
        league_code = self.fishy_league_mapping.get(url)
        if not league_code:
            raise ValueError(f"Unknown URL for TheFishy scraper: {url}")
        
        page_content = get_fishy_page_content_selenium(url)
        league_data = parse_fishy_league_standing_data(page_content)
        
        # Assuming league_data contains the required fields matching CurrentLeague model
        for team_standing in league_data:
            current_league_data = {
                'team_id': team_standing['team_id'],
                'league_id': team_standing['league_id'],
                'season_id': team_standing['season_id'],
                'position': team_standing['position'],
                'played': team_standing['played'],
                'wins': team_standing['wins'],
                'draws': team_standing['draws'],
                'losses': team_standing['losses'],
                'goals_for': team_standing['goals_for'],
                'goals_against': team_standing['goals_against'],
                'goal_difference': team_standing['goal_difference'],
                'points': team_standing['points'],
                'league_code': league_code  # Adding the league code
            }
            self.current_league_service.create_current_league(current_league_data)
