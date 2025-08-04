import json
import urllib.request
import urllib.error
import pytz
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.new_odds.services.new_odds_service import NewOddsService
from app.teams.services.team_service import TeamService
from app.leagues.services.league_service import LeagueService

class BetfairService:
    def __init__(self, db: Session):
        self.db = db
        self.appKey = "OTCBYdanqSKplEmM"
        self.sessionToken = "+ilb0ba/KTaMVc8zvL6IcWFC1Ogzo78LMQlW0UmGr1M="
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
        # target_names = [
        #         "English Premier League", "English Championship",
        #         "Scottish Premiership", "Scottish Championship",
        #         "Spanish La Liga", "Spanish Segunda",
        #         "Italian Serie A", "Italian Serie B",
        #         "German Bundesliga", "German Bundesliga 2", "Turkish Super League", "French Ligue 1"
        # ]
        target_names = [
                "English Premier League","English Championship","Scottish Premiership","Scottish Championship",
                "German Bundesliga 2",
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

   

    def display_filtered_competitions_and_markets(self):
        print("\n=== Filtered Competitions ===")
        filtered_comps = self.get_filtered_competitions()

        competitions_data = []

        for key, comp in filtered_comps.items():
            print(f"{key} - {comp['name']}")

        for key, comp in filtered_comps.items():
            comp_dict = {
                "competition_name": comp['name'],
                "competition_id": comp['id'],
                "events": []
            }

            print(f"\nFetching matches for: {comp['name']}")
            comp_id = comp['id']
            res = self.list_events("1", comp_id)

            if not res or "result" not in res:
                print("No events found.")
                continue

            for ev in res["result"]:
                event = ev['event']
                event_id = event['id']
                event_name = event['name']
                event_time = event['openDate']
                # event_time = datetime.strptime(event['openDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
                # event_time = event_time.replace(tzinfo=pytz.utc)
                # london_time = event_time.astimezone(pytz.timezone("Europe/London"))

                # Drop the timezone and format as string
                # formatted_time = london_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                event_dict = {
                    "event_id": event_id,
                    "event_name": event_name,
                    "start_time": event_time,
                    "markets": []
                }

                market_types = ["MATCH_ODDS", "OVER_UNDER_25", "OVER_UNDER_15", "OVER_UNDER_35"]
                mc_res = self.list_market_catalogue(event_id, market_types)

                if not mc_res or "result" not in mc_res or len(mc_res["result"]) == 0:
                    continue

                market_ids = [m["marketId"] for m in mc_res["result"]]
                mb_res = self.list_market_book(market_ids)
                if not mb_res or "result" not in mb_res:
                    continue

                market_book_map = {m["marketId"]: m for m in mb_res["result"]}

                for market in mc_res["result"]:
                    market_id = market["marketId"]
                    market_name = market.get("marketName", "N/A")
                    start_time = market.get("marketStartTime", "N/A")
                    runners = market.get("runners", [])
                    book = market_book_map.get(market_id, {})

                    market_dict = {
                        "market_id": market_id,
                        "market_name": market_name,
                        "start_time": start_time,
                        "selections": []
                    }

                    for runner in runners:
                        selection_id = runner["selectionId"]
                        runner_name = runner["runnerName"]

                        book_runner = next(
                            (r for r in book.get("runners", []) if r["selectionId"] == selection_id), None)

                        best_back = best_lay = None
                        if book_runner:
                            backs = book_runner.get("ex", {}).get("availableToBack", [])
                            lays = book_runner.get("ex", {}).get("availableToLay", [])
                            if backs:
                                best_back = {
                                    "price": backs[0]["price"],
                                    "size": backs[0]["size"]
                                }
                            if lays:
                                best_lay = {
                                    "price": lays[0]["price"],
                                    "size": lays[0]["size"]
                                }

                        market_dict["selections"].append({
                            "selection_id": selection_id,
                            "name": runner_name,
                            "best_back": best_back,
                            "best_lay": best_lay
                        })

                    event_dict["markets"].append(market_dict)

                comp_dict["events"].append(event_dict)

            competitions_data.append(comp_dict)

            # Save after processing all events for the competition
            for event_dict in comp_dict["events"]:
                try:
                    self.transform_and_save_betfair_odds(event_dict, comp_dict["competition_name"])
                except Exception as e:
                    print(f"Error saving odds for event {event_dict.get('event_name')} in competition {comp_dict['competition_name']}: {e}")


    def transform_and_save_betfair_odds(self, event_dict: Dict, competition_name: str) -> None:
        """
        Transforms already structured event data and saves MATCH_ODDS to the DB.

        Args:
            event_dict: A single event dictionary from the structured JSON
            competition_name: Name of the competition to map league
        """
        event_name = event_dict["event_name"]
        start_time = datetime.strptime(event_dict["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ")

        # Map competition to league code
        league_code = self.map_betfair_competition_to_league(competition_name)
        if not league_code:
            print(f"Unsupported league: {competition_name} for {event_name}")
            return

        # Parse team names
        try:
            home_team, away_team = self.parse_teams_from_event(event_name)
        except ValueError as e:
            print(f"Parse error for {event_name}: {e}")
            return

        # Find MATCH_ODDS market
        match_market = next(
            (m for m in event_dict["markets"] if m["market_name"].lower().replace(" ", "") == "matchodds"),
            None
        )

        if not match_market:
            print(f"No MATCH_ODDS market found for {event_name}")
            return

        # Extract odds
        home_odds = draw_odds = away_odds = None
        for sel in match_market["selections"]:
            name = sel["name"].lower()
            best_back = sel.get("best_back", {})
            price = best_back.get("price") if best_back else None

            if price:
                if name == home_team.lower():
                    home_odds = price
                elif "draw" in name:
                    draw_odds = price
                elif name == away_team.lower():
                    away_odds = price
        print(f"Extracted odds for {event_name}: Home={home_odds}, Draw={draw_odds}, Away={away_odds}")
        if not all([home_odds, draw_odds, away_odds]):
            print(f"Incomplete odds for {event_name} - skipping")
            return
        full_event_json = json.dumps(event_dict)
        odds_data = {
            'date': start_time.date(),
            'time': start_time.time(),
            'home_team_id': self.team_service.get_or_create_team(home_team, league_code).team_id,
            'away_team_id': self.team_service.get_or_create_team(away_team, league_code).team_id,
            'home_odds': home_odds,
            'draw_odds': draw_odds,
            'away_odds': away_odds,
            'league_code': league_code,
            'full_market_data': full_event_json
        }

        print(f"Saving Odds: {event_name} | H {home_odds} | D {draw_odds} | A {away_odds}")
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

    def map_betfair_competition_to_league(self, betfair_comp_name: str) -> Optional[str]:
        """Maps Betfair competition IDs to your league codes."""
        league_mapping = {
            "English Premier League": "E0",  # English Premier League
            "English Championship": "E1",  # English Championship
            "Scottish Premiership": "SC0", # Scottish Premiership
            "Scottish Championship": "SC1", # Scottish Championship
            "Spanish La Liga": "SP1",  # Spanish Segunda
            "Spanish Segunda": "SP2",  # Spanish Segunda
            "German Bundesliga": "D1",  
            "German Bundesliga 2": "D2",  
            "Italian Serie A": "I1",  
            "Italian Serie B": "I2",  
            "French Ligue 1": "F1",  
            "Turkish Super League": "T1",  

        }
        return league_mapping.get(str(betfair_comp_name))

    