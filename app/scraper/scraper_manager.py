from app.scraper.oddsportal.oddsportal_scraper.oddsportal_scraper import get_odds_page_content, parse_match_data
from app.scraper.fishy.fishy_scraper.fishy_scraper import get_fishy_page_content, parse_fishy_league_standing_data
from app.scraper.betfair.betfair_scraper.betfair_scraper import get_betfair_page_content, parse_betfair_match_data  # You'll need to put your Betfair functions in this module
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
            "https://www.oddsportal.com/football/scotland/championship/": "SC1",
            "https://www.oddsportal.com/football/turkey/super-lig/": "T1",
            "https://www.oddsportal.com/football/italy/serie-a/": "I1",
            "https://www.oddsportal.com/football/italy/serie-b/": "I2",
            "https://www.oddsportal.com/football/spain/laliga/": "SP1",
            "https://www.oddsportal.com/football/spain/laliga2/": "SP2",
            "https://www.oddsportal.com/football/germany/bundesliga/": "D1",
            "https://www.oddsportal.com/football/germany/2-bundesliga/": "D2",
        }

        # Mapping URLs to league codes for TheFishy
        self.fishy_league_mapping = {
            "https://thefishy.co.uk/leaguetable.php?table=1": "E0",  # Premier League
            "https://thefishy.co.uk/leaguetable.php?table=2": "E1",  # Championship
            "https://thefishy.co.uk/leaguetable.php?table=10": "SC0", # Scottish Premier League
            "https://thefishy.co.uk/leaguetable.php?table=11": "SC1",  # Scottish Championship
            "https://thefishy.co.uk/leaguetable.php?table=79": "T1",
            "https://thefishy.co.uk/leaguetable.php?table=33": "I1",
            "https://thefishy.co.uk/leaguetable.php?table=83": "I2",
            "https://thefishy.co.uk/leaguetable.php?table=31": "SP1",
            "https://thefishy.co.uk/leaguetable.php?table=81": "SP2",
            "https://thefishy.co.uk/leaguetable.php?table=32": "D1",
            "https://thefishy.co.uk/leaguetable.php?table=82": "D2",
            "https://thefishy.co.uk/leaguetable.php?table=34": "F1",
        }
    
    def run_scraper(self, url):
        if self.scraper_name == 'oddsportal':
            return self._run_oddsportal_scraper(url)
        elif self.scraper_name == 'thefishy':
            return self._run_fishy_scraper(url)
        else:
            raise ValueError("Unsupported scraper name")
    
    async def _run_oddsportal_scraper(self, url):
        try:
            league_code = self.oddsportal_league_mapping.get(url)
            if not league_code:
                raise ValueError(f"Unknown URL for OddsPortal scraper: {url}")

            page_content = await get_odds_page_content(url)
            match_data = parse_match_data(page_content)

            for match in match_data:
                home_team = self.team_service.get_or_create_team(match['Home Team'], league_code)
                away_team = self.team_service.get_or_create_team(match['Away Team'], league_code)
                
                if not home_team or not away_team:
                    print(f"Warning: Could not find or create teams for {match['Home Team']} or {match['Away Team']}")
                    continue
                
                new_odds_data = {
                    'date': match['Date'],
                    'time': match['Time'],
                    'home_team_id': home_team.team_id,
                    'away_team_id': away_team.team_id,
                    'home_odds': match['Home Odds'],
                    'draw_odds': match['Draw Odds'],
                    'away_odds': match['Away Odds'],
                    'league_code': league_code
                }
                print("New odds data:", new_odds_data)
                self.new_odds_service.create_new_odds(new_odds_data)

            return "OddsPortal Scraping: Success"
        except Exception as e:
            return f"OddsPortal Scraping: Failed - {str(e)}"
    
    async def _run_fishy_scraper(self, url):
        try:
            league_code = self.fishy_league_mapping.get(url)
            if not league_code:
                raise ValueError(f"Unknown URL for TheFishy scraper: {url}")

            page_content = await get_fishy_page_content(url)
            print(f"[DEBUG] Got page content for {url} (length={len(page_content)})")

            league_data = parse_fishy_league_standing_data(page_content)
            print(f"[DEBUG] Parsed {len(league_data)} teams from {url}")

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
                    'league_code': league_code
                }
                print("Current league data:", current_league_data)
                self.current_league_service.create_or_update_current_league(current_league_data)

            return "TheFishy Scraping: Success"
        except Exception as e:
            return f"TheFishy Scraping: Failed - {str(e)}"
        


    async def _run_betfair_scraper(self, url):
        try:
            # Fetch page content with Selenium
            page_content = await get_betfair_page_content(url)

            # Parse data from page content
            match_data = parse_betfair_match_data(page_content)

            print(f"[DEBUG] Parsed Betfair match data: {match_data}")
            return match_data

        except Exception as e:
            print(f"[ERROR] Betfair scraping failed: {e}")
            return None