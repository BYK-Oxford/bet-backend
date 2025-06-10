import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.new_odds.services.new_odds_service import NewOddsService
from app.teams.services.team_service import TeamService
from app.leagues.services.league_service import LeagueService

class BetfairService:
    def __init__(self, db: Session):
        self.db = db
        self.appKey = "OTCBYdanqSKplEmM"
        self.sessionToken = "Ef17NEA5AuoWhIR9FWsBmzi1HYfk8tMB/HQPt54kVtY="
        self.url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
        
        # Initialize services
        self.new_odds_service = NewOddsService(db)
        self.team_service = TeamService(db)
        self.league_service = LeagueService(db)

    def call_aping(self, jsonrpc_req: Dict) -> Optional[Dict]:
        headers = {
            'X-Application': self.appKey,
            'X-Authentication': self.sessionToken,
            'Content-Type': 'application/json'
        }
        data = json.dumps(jsonrpc_req).encode('utf-8')
        req = urllib.request.Request(self.url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                resp_data = response.read().decode('utf-8')
                return json.loads(resp_data)
        except urllib.error.URLError as e:
            print(f"Network error: {e}")
        except urllib.error.HTTPError as e:
            print(f"HTTP error: {e}")
        return None

    def list_competitions(self, event_type_id: str) -> Optional[Dict]:
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listCompetitions",
            "params": {"filter": {"eventTypeIds": [event_type_id]}},
            "id": 2
        }
        return self.call_aping(req)

    def list_events(self, event_type_id: str, competition_id: Optional[str] = None) -> Optional[Dict]:
        filter_obj = {
            "eventTypeIds": [event_type_id],
        }
        if competition_id:
            filter_obj["competitionIds"] = [competition_id]
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listEvents",
            "params": {"filter": filter_obj},
            "id": 3
        }
        return self.call_aping(req)

    def list_market_catalogue(self, event_id: str, market_types: List[str]) -> Optional[Dict]:
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketCatalogue",
            "params": {
                "filter": {
                    "eventIds": [event_id],
                    "marketTypeCodes": market_types
                },
                "maxResults": 200,
                # FIXED: Include COMPETITION in marketProjection to get competition data
                "marketProjection": ["COMPETITION", "EVENT", "MARKET_START_TIME", "RUNNER_DESCRIPTION"]
            },
            "id": 6
        }
        return self.call_aping(req)

    def list_market_book(self, market_ids: List[str]) -> Optional[Dict]:
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketBook",
            "params": {
                "marketIds": market_ids,
                "priceProjection": {"priceData": ["EX_BEST_OFFERS"]}
            },
            "id": 5
        }
        return self.call_aping(req)

    def get_filtered_competitions(self) -> Dict[str, Dict]:
        target_names = [
            "Spanish Segunda", "Brazilian U20", 
        ]
        event_type_id = "1"  # Soccer
        res = self.list_competitions(event_type_id)
        competitions_map = {}
        idx = 1
        if res and "result" in res:
            for comp in res["result"]:
                comp_name = comp['competition']['name']
                if any(target.lower() in comp_name.lower() for target in target_names):
                    comp_id = comp['competition']['id']
                    competitions_map[str(idx)] = {"id": comp_id, "name": comp_name}
                    idx += 1
        return competitions_map

    def transform_and_save_betfair_odds(self, event_data: Dict, market_data: List[Dict]) -> None:
        """
        Transforms Betfair API data to match your database schema.
        Args:
            event_data: Raw event data from listEvents
            market_data: Raw market catalogue data (not market book)
        """
        # FIXED: Get competition info from market catalogue instead of event data
        if not market_data:
            print(f"No market data provided")
            return
            
        # Get the first market to extract competition info
        first_market = market_data[0]
        
        # Check if competition info exists in market data
        if 'competition' not in first_market:
            print(f"No competition info in market data for event: {event_data['event']['name']}")
            return
        
        # Extract event details
        event_name = event_data['event']['name']
        event_time = datetime.strptime(
            event_data['event']['openDate'], 
            "%Y-%m-%dT%H:%M:%S.%fZ"  # Betfair's time format
        )
        
        # Parse teams from event name (e.g., "Man Utd v Arsenal")
        try:
            home_team, away_team = self.parse_teams_from_event(event_name)
        except ValueError as e:
            print(f"Failed to parse teams: {e}")
            return
        
        # FIXED: Get league code from market data instead of event data
        league_code = self.map_betfair_competition_to_league(
            first_market['competition']['id']
        )
        
        # Skip if league not supported
        if not league_code:
            print(f"Skipping unsupported league: {event_name} (Competition ID: {first_market['competition']['id']})")
            return

        LEAGUE_NAME_MAPPING = {
            'E0': 'English Premier League',
            'E1': 'English Championship',
            'SC0': 'Scottish Premier League',
            'SC1': 'Scottish Championship',
            'T1': 'Süper Lig',
            'I1': 'Serie A',
            'I2': 'Serie B',
            'SP1': 'La Liga',
            'SP2': 'La Liga 2',
            'D1': 'Bundesliga',
            'D2': 'Bundesliga 2',
            'B20': 'Brazilian U20',
            'S2': 'Spanish Segunda División' 
        }
        league_name = LEAGUE_NAME_MAPPING.get(league_code)
        
        # Get or create teams
        home_team_db = self.team_service.get_or_create_team(home_team, league_name)
        away_team_db = self.team_service.get_or_create_team(away_team, league_name)
        
        # Get market book data for odds
        market_ids = [m["marketId"] for m in market_data]
        market_books = self.list_market_book(market_ids)
        
        if not market_books or "result" not in market_books:
            print(f"No market book data for {event_name}")
            return
        
        # Extract odds from market book data (MATCH_ODDS market)
        match_odds_book = next(
            (m for m in market_books["result"] if any(
                mc["marketName"] == "MATCH_ODDS" and mc["marketId"] == m["marketId"] 
                for mc in market_data
            )), 
            None
        )
        
        if not match_odds_book:
            print(f"No match odds found for {event_name}")
            return

        # Prepare data for NewOddsService
        odds_data = {
            'date': event_time.date(),
            'time': event_time.time(),
            'home_team_id': home_team_db.team_id,
            'away_team_id': away_team_db.team_id,
            'home_odds': self.get_runner_price_from_book(match_odds_book, home_team),
            'draw_odds': self.get_runner_price_from_book(match_odds_book, 'Draw'),
            'away_odds': self.get_runner_price_from_book(match_odds_book, away_team),
            'league_code': league_code
        }
        
        # Save to database
        self.new_odds_service.create_new_odds(odds_data)

    def parse_teams_from_event(self, event_name: str) -> tuple:
        """Splits 'Team A v Team B' into two team names."""
        parts = event_name.split(' v ')
        if len(parts) != 2:
            raise ValueError(f"Unexpected event name format: {event_name}")
        return parts[0].strip(), parts[1].strip()

    def get_runner_price_from_book(self, market_book_data: Dict, runner_name: str) -> Optional[float]:
        """Extracts the best back price for a runner from market book data."""
        # Market book data doesn't have runnerName, need to match by selection ID
        # This is more complex - you might need to match runners from catalogue to book
        runners = market_book_data.get('runners', [])
        if runners and len(runners) > 0:
            # For now, return the first available price
            first_runner = runners[0]
            if 'ex' in first_runner and first_runner['ex'].get('availableToBack'):
                return first_runner['ex']['availableToBack'][0]['price']
        return None

    def map_betfair_competition_to_league(self, betfair_comp_id: str) -> Optional[str]:
        """Maps Betfair competition IDs to your league codes."""
        league_mapping = {
            "10932509": "E0",  # English Premier League
            "10932510": "E1",  # English Championship
            "10932513": "SC0", # Scottish Premiership
            "12204313": "S2",  # Spanish Segunda
            "12148223": "B20", # Brazilian U20
        }
        return league_mapping.get(str(betfair_comp_id))

    def get_betfair_odds(self) -> None:
        filtered_comps = self.get_filtered_competitions()
        
        for comp in filtered_comps.values():
            events = self.list_events("1", comp['id'])
            if not events or "result" not in events:
                continue
                
            for event in events["result"]:
                market_types = ["MATCH_ODDS"]
                markets = self.list_market_catalogue(event['event']['id'], market_types)
                
                if markets and "result" in markets:
                    # FIXED: Pass market catalogue result instead of market book result
                    self.transform_and_save_betfair_odds(
                        event, 
                        markets["result"]  # This contains competition info
                    )