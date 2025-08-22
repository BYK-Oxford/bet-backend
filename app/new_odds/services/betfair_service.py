import json
import re
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
from app.core.betfair_auth import BetfairAuthService

class BetfairService:
    def __init__(self, db: Session):
        self.db = db
        self.appKey = "OTCBYdanqSKplEmM"
        #self.sessionToken = "O43pZ76JoNaTP2Krb9RWLQub/x5x53FH+n6kXoX6Ifc="
        self.url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

        # Hardcoded credentials and cert path here:
        self.username = "Sharburrys07@yahoo.com"
        self.password = "BYK0xf0rd!"
        
        self.sessionToken = None
        
        # Authenticate right away
        self.authenticate()
        
        # Initialize services
        self.new_odds_service = NewOddsService(db)
        self.team_service = TeamService(db)
        self.league_service = LeagueService(db)


    def authenticate(self):
        auth_service = BetfairAuthService(self.username, self.password,  self.appKey)
        token = auth_service.get_session_token()
        if token:
            self.sessionToken = token
            print("Token:" ,self.sessionToken)
            print("Token generated:" ,token)
            print("Successfully authenticated.")
        else:
            raise Exception("Authentication failed.")


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
                "English Premier League","English Sky Bet Championship","Scottish Premiership",
                "Scottish Championship","Turkish Super League","Spanish La Liga","Spanish Segunda Division",
                "German Bundesliga","German Bundesliga 2","French Ligue 1", "Italian Serie A", "Italian Serie B"
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
            "English Sky Bet Championship": "E1",  # English Championship
            "Scottish Premiership": "SC0", # Scottish Premiership
            "Scottish Championship": "SC1", # Scottish Championship
            "Spanish La Liga": "SP1",  # Spanish La Liga
            "Spanish Segunda Division": "SP2",  # Spanish Segunda Division
            "German Bundesliga": "D1",  
            "German Bundesliga 2": "D2",  
            "Italian Serie A": "I1",  
            "Italian Serie B": "I2",  
            "French Ligue 1": "F1",  
            "Turkish Super League": "T1",  

        }
        return league_mapping.get(str(betfair_comp_name))

    def get_live_games_by_league(self) -> list[dict]:
        """
        Get all in-play football games from selected leagues with odds and URLs.

        Returns:
            List of dicts: {
                "event_id": str,
                "standard_url": str,
                "exchange_url": str,
                "home_odds": str,
                "draw_odds": str,
                "away_odds": str
            }
        """
        from math import ceil

        def slugify(text):
            text = text.lower()
            text = text.replace("&", "and")
            text = re.sub(r"[\'()]", "-", text)
            text = re.sub(r"[^a-z0-9\s-]", "", text)
            text = re.sub(r"\s+", "-", text)
            text = re.sub(r"-{2,}", "-", text)
            return text.strip("-")
        
        
        selected_league_names = [v["name"] for v in self.get_filtered_competitions().values()] 

        # Step 1: List all in-play football MATCH_ODDS markets
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketCatalogue",
            "params": {
                "filter": {
                    "eventTypeIds": ["1"],  # Soccer
                    "inPlayOnly": True,
                    "marketTypeCodes": ["MATCH_ODDS"]
                },
                "maxResults": 100,
                "marketProjection": ["COMPETITION", "EVENT", "MARKET_START_TIME", "RUNNER_DESCRIPTION"]
            },
            "id": 7
        }

        res = self.call_aping(req)
        print("Total games available: ",len(res["result"]))
        if not res or "result" not in res or len(res["result"]) == 0:
            print("⚠️ No in-play markets found.")
            return []

        market_ids = [market["marketId"] for market in res["result"]]
        market_book_map = {}
        chunk_size = 40

        # Step 2: Get price data for each market
        for i in range(0, len(market_ids), chunk_size):
            chunk = market_ids[i:i + chunk_size]
            books = self.list_market_book(chunk)
            if books and "result" in books:
                for book in books["result"]:
                    market_book_map[book["marketId"]] = book

        # Step 3: Process and filter results
        live_games = []
        for market in res["result"]:
            comp_name = market.get('competition', {}).get('name', '').strip()
            if not comp_name:
                continue

            if not any(comp_name.lower() == league.lower() for league in selected_league_names):
                continue

            event = market["event"]
            runners = market["runners"]
            market_id = market["marketId"]
            event_id = event["id"]

            comp_slug = slugify(comp_name)
            match_slug = slugify(event["name"])

            standard_url = f"https://www.betfair.com/betting/football/{comp_slug}/{match_slug}/e-{event_id}"
            exchange_url = f"https://www.betfair.com/exchange/plus/en/football/{comp_slug}/{match_slug}-betting-{event_id}"

            book = market_book_map.get(market_id)
            if not book:
                continue

            runner_odds = {}
            for runner in runners:
                selection_id = runner["selectionId"]
                runner_name = runner["runnerName"]
                runner_book = next((r for r in book["runners"] if r["selectionId"] == selection_id), None)

                if runner_book:
                    backs = runner_book.get("ex", {}).get("availableToBack", [])
                    best_back_price = f"{backs[0]['price']}" if backs else "N/A"
                    runner_odds[runner_name.lower()] = best_back_price

            # Ensure we have all three: home, draw, away
            home, draw, away = "N/A", "N/A", "N/A"
            if len(runners) == 3:
                home = runner_odds.get(runners[0]["runnerName"].lower(), "N/A")
                draw = runner_odds.get(runners[1]["runnerName"].lower(), "N/A")
                away = runner_odds.get(runners[2]["runnerName"].lower(), "N/A")

            game_data = {
                "event_id": event_id,
                "standard_url": standard_url,
                "exchange_url": exchange_url,
                "home_odds": home,
                "draw_odds": draw,
                "away_odds": away,
            }
            live_games.append(game_data)

        return live_games