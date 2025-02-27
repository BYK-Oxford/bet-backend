from oddsportal.oddsportal_scraper.oddsportal_scraper import get_page_content_selenium, parse_match_data
from fishy.fishy_scraper.fishy_scraper import get_fishy_page_content_selenium, parse_fishy_league_standing_data
from app.new_odds.services.new_odds_service import NewOddsService
from app.current_league.services.current_league_service import CurrentLeagueService


class ScraperManager:
    def __init__(self, scraper_name):
        self.scraper_name = scraper_name
        self.new_odds_service = NewOddsService()
        self.current_league_service = CurrentLeagueService()
    
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
        
        # Assuming match_data contains the required fields matching NewOdds model
        for match in match_data:
            new_odds_data = {
                'new_odds_id': match['id'],  # Generate appropriate ID
                'date': match['date'],
                'time': match['time'],
                'home_team_id': match['home_team_id'],
                'away_team_id': match['away_team_id'],
                'home_odds': match['home_odds'],
                'draw_odds': match['draw_odds'],
                'away_odds': match['away_odds']
            }
            self.new_odds_service.create_new_odds(new_odds_data)
    
    def _run_fishy_scraper(self, url):
        page_content = get_fishy_page_content_selenium(url)
        league_data = parse_fishy_league_standing_data(page_content)
        
        # Assuming league_data contains the required fields matching CurrentLeague model
        for team_standing in league_data:
            current_league_data = {
                'current_league_id': team_standing['id'],  # Generate appropriate ID
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
                'points': team_standing['points']
            }
            self.current_league_service.create_current_league(current_league_data)

