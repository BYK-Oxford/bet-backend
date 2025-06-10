import json
import urllib.request
import urllib.error
from datetime import datetime
from app.new_odds.services.new_odds_service import NewOddsService
from app.teams.services.team_service import TeamService
from app.leagues.services.league_service import LeagueService

# Betfair API credentials (replace with your actual values)
appKey = "OTCBYdanqSKplEmM"
sessionToken = "Ef17NEA5AuoWhIR9FWsBmzi1HYfk8tMB/HQPt54kVtY="

url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

def call_aping(jsonrpc_req):
    headers = {
        'X-Application': appKey,
        'X-Authentication': sessionToken,
        'Content-Type': 'application/json'
    }
    data = json.dumps(jsonrpc_req).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            resp_data = response.read().decode('utf-8')
            return json.loads(resp_data)
    except urllib.error.URLError as e:
        print(f"Network error: {e}")
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e}")
    return None

def list_competitions(event_type_id):
    req = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listCompetitions",
        "params": {"filter": {"eventTypeIds": [event_type_id]}},
        "id": 2
    }
    return call_aping(req)

def list_events(event_type_id, competition_id=None):
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
    return call_aping(req)

def list_market_catalogue(event_id, market_types):
    req = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketCatalogue",
        "params": {
            "filter": {
                "eventIds": [event_id],
                "marketTypeCodes": market_types
            },
            "maxResults": 200,
            "marketProjection": ["MARKET_START_TIME", "RUNNER_DESCRIPTION"]
        },
        "id": 6
    }
    return call_aping(req)

def list_market_book(market_ids):
    req = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketBook",
        "params": {
            "marketIds": market_ids,
            "priceProjection": {"priceData": ["EX_BEST_OFFERS"]}
        },
        "id": 5
    }
    return call_aping(req)

def get_filtered_competitions():
    # target_names = [
    #     "English Premier League", "English League 1", "English League 2",
    #     "Scottish Premiership", "Scottish Championship",
    #     "Spanish La Liga", "Spanish Segunda",
    #     "Italian Serie A", "Italian Serie B",
    #     "German Bundesliga", "German Bundesliga 2",
    #     "Turkish Super Lig", "Brazilian U20", "Ecuadorian Serie A", "Norwegian 3rd Division"
    # ]
    target_names = [
         "Spanish Segunda", "Brazilian U20", 
    ]

    event_type_id = "1"  # Soccer
    res = list_competitions(event_type_id)
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


def transform_and_save_betfair_odds(db, event_data, market_data):
    """
    Transforms Betfair API data to match your database schema.
    Args:
        db: SQLAlchemy Session
        event_data: Raw event data from listEvents
        market_data: Raw market data from listMarketBook
    """
    new_odds_service = NewOddsService(db)
    team_service = TeamService(db)
    league_service = LeagueService(db)

    # Extract event details
    event_name = event_data['event']['name']
    event_time = datetime.strptime(
        event_data['event']['openDate'], 
        "%Y-%m-%dT%H:%M:%S.%fZ"  # Betfair's time format
    )
    
    # Parse teams from event name (e.g., "Man Utd vs Arsenal")
    home_team, away_team = parse_teams_from_event(event_name)
    
    # Get league code (you'll need to map Betfair competition to your league codes)
    league_code = map_betfair_competition_to_league(
        event_data['event']['competition']['id']
    )
    
    # Skip if league not supported
    if not league_code:
        print(f"Skipping unsupported league: {event_name}")
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
        # Add more mappings as needed
    }
    league_name = LEAGUE_NAME_MAPPING.get(league_code)
    # Get or create teams
    home_team_db = team_service.get_or_create_team(home_team, league_name)
    away_team_db = team_service.get_or_create_team(away_team, league_name)

    # Extract odds from market data (MATCH_ODDS market)
    match_odds = next(
        (m for m in market_data if m['marketName'] == 'MATCH_ODDS'), 
        None
    )
    
    if not match_odds:
        print(f"No match odds found for {event_name}")
        return

    # Prepare data for NewOddsService
    odds_data = {
        'date': event_time.date(),
        'time': event_time.time(),
        'home_team_id': home_team_db.team_id,
        'away_team_id': away_team_db.team_id,
        'home_odds': get_runner_price(match_odds, home_team_db.name),
        'draw_odds': get_runner_price(match_odds, 'Draw'),
        'away_odds': get_runner_price(match_odds, away_team_db.name),
        'league_code': league_code
    }
    
    # Save to database
    new_odds_service.create_new_odds(odds_data)

def parse_teams_from_event(event_name):
    """Splits 'Team A v Team B' into two team names."""
    parts = event_name.split(' v ')
    if len(parts) != 2:
        raise ValueError(f"Unexpected event name format: {event_name}")
    return parts[0].strip(), parts[1].strip()

def get_runner_price(market_data, runner_name):
    """Extracts the best back price for a runner."""
    runner = next(
        (r for r in market_data['runners'] 
         if r['runnerName'] == runner_name), 
        None
    )
    if runner and 'ex' in runner and runner['ex']['availableToBack']:
        return runner['ex']['availableToBack'][0]['price']
    return None

def map_betfair_competition_to_league(betfair_comp_id):
    """Maps Betfair competition IDs to your league codes."""
    league_mapping = {
        "10932509": "E0",  # English Premier League
        "10932510": "E1",  # English Championship
        "10932513": "SC0", # Scottish Premiership
        "12204313": "S2",  # English Championship
        "12148223": "B20", # Scottish Premiership
        # Add more mappings as needed
    }
    return league_mapping.get(str(betfair_comp_id))

def get_betfair_odds(db):
    filtered_comps = get_filtered_competitions()
    
    for comp in filtered_comps.values():
        events = list_events("1", comp['id'])
        if not events or "result" not in events:
            continue
            
        for event in events["result"]:
            market_types = ["MATCH_ODDS"]
            markets = list_market_catalogue(event['event']['id'], market_types)
            
            if markets and "result" in markets:
                market_ids = [m["marketId"] for m in markets["result"]]
                market_books = list_market_book(market_ids)
                
                if market_books and "result" in market_books:
                    transform_and_save_betfair_odds(
                        db, 
                        event, 
                        market_books["result"]
                    )