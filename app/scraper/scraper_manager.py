from app.scraper.oddsportal.oddsportal_scraper.oddsportal_scraper import get_odds_page_content, parse_match_data
from app.scraper.fishy.fishy_scraper.fishy_scraper import get_fishy_page_content, parse_fishy_league_standing_data
from app.new_odds.services.new_odds_service import NewOddsService
from app.current_league.services.current_league_service import CurrentLeagueService
from app.teams.services.team_service import TeamService
from sqlalchemy.orm import Session

class ScraperManager:
    def __init__(self, scraper_name, db: Session):
        self.scraper_name = scraper_name
        self.new_odds_service = NewOddsService(db)
        self.current_league_service = CurrentLeagueService(db)
        self.team_service = TeamService(db)
        
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
        league_code = self.oddsportal_league_mapping.get(url)
        if not league_code:
            raise ValueError(f"Unknown URL for OddsPortal scraper: {url}")
        
        page_content = get_odds_page_content(url)
        match_data = parse_match_data(page_content)
        
        for match in match_data:
            # Get team objects using TeamService
            home_team = self.team_service.get_or_create_team(match['Home Team'], league_code)
            away_team = self.team_service.get_or_create_team(match['Away Team'], league_code)
            
            if not home_team or not away_team:
                print(f"Warning: Could not find or create teams for {match['Home Team']} or {match['Away Team']}")
                continue
                
            new_odds_data = {
                'date': match['Date'],
                'time': match['Time'],
                'home_team_id': home_team.team_id,  # Using the actual team ID from database
                'away_team_id': away_team.team_id,  # Using the actual team ID from database
                'home_odds': match['Home Odds'],
                'draw_odds': match['Draw Odds'],
                'away_odds': match['Away Odds'],
                'league_code': league_code
            }
            print("New odds data:", new_odds_data)
            self.new_odds_service.create_new_odds(new_odds_data)
    
    def _run_fishy_scraper(self, url):
        # Get league code from the URL mapping for TheFishy
        league_code = self.fishy_league_mapping.get(url)
        if not league_code:
            raise ValueError(f"Unknown URL for TheFishy scraper: {url}")
        
        page_content = get_fishy_page_content(url)
        league_data = parse_fishy_league_standing_data(page_content)
        
        # Assuming league_data contains the required fields matching CurrentLeague model
        for team_standing in league_data:
            current_league_data = {
                'team_id': team_standing['Team'],
                'year': team_standing['Year'],
                'position': team_standing['Position'],
                'played': team_standing['Played'],
                'wins': team_standing['Wins'],
                'draws': team_standing['Draws'],
                'losses': team_standing['Losses'],
                'goals_for': team_standing['Goals For'],
                'goals_against': team_standing['Goals Against'],
                'goal_difference': team_standing['Goal Difference'],
                'points': team_standing['Points'],
                'league_code': league_code  # Adding the league code
            }
            print("Current league data:", current_league_data)
            self.current_league_service.create_or_update_current_league(current_league_data)
