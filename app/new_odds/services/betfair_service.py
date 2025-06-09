import json
import urllib.request
import urllib.error

# Betfair API credentials (replace with your actual values)
appKey = "OTCBYdanqSKplEmM"
sessionToken = "CO8gXBTzLRCC69/5HoTLhX4H25ULEJTpitTgBM6/FBI="

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
    target_names = [
        "English Premier League", "English League 1", "English League 2",
        "Scottish Premiership", "Scottish Championship",
        "Spanish La Liga", "Spanish Segunda",
        "Italian Serie A", "Italian Serie B",
        "German Bundesliga", "German Bundesliga 2",
        "Turkish Super Lig", "Brazilian U20", "Ecuadorian Serie A", "Norwegian 3rd Division"
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

def get_betfair_odds():
    filtered_comps = get_filtered_competitions()
    print("\n=== Filtered Competitions ===")
    for key, comp in filtered_comps.items():
        print(f"{key} - {comp['name']}")

    for key, comp in filtered_comps.items():
        print(f"\nFetching matches for: {comp['name']}")
        comp_id = comp['id']
        res = list_events("1", comp_id)

        if not res or "result" not in res:
            print("No events found.")
            continue

        for ev in res["result"]:
            event = ev['event']
            event_id = event['id']
            event_name = event['name']
            event_time = event['openDate']
            print(f"\n🔹 Event: {event_name} (ID: {event_id}) at {event_time}")

            market_types = ["MATCH_ODDS", "OVER_UNDER_25", "OVER_UNDER_15", "OVER_UNDER_35"]
            mc_res = list_market_catalogue(event_id, market_types)
            if not mc_res or "result" not in mc_res or len(mc_res["result"]) == 0:
                print("No market catalogue found.")
                continue

            market_ids = [m["marketId"] for m in mc_res["result"]]
            mb_res = list_market_book(market_ids)
            if not mb_res or "result" not in mb_res:
                print("No market book found.")
                continue

            market_book_map = {m["marketId"]: m for m in mb_res["result"]}

            for market in mc_res["result"]:
                market_id = market["marketId"]
                market_name = market.get("marketName", "N/A")
                start_time = market.get("marketStartTime", "N/A")
                runners = market.get("runners", [])
                book = market_book_map.get(market_id, {})

                print(f"  ➤ Market: {market_name} (ID: {market_id}) | Start: {start_time}")

                for runner in runners:
                    selection_id = runner["selectionId"]
                    runner_name = runner["runnerName"]

                    book_runner = next(
                        (r for r in book.get("runners", []) if r["selectionId"] == selection_id), None)

                    best_back = best_lay = "N/A"
                    if book_runner:
                        backs = book_runner.get("ex", {}).get("availableToBack", [])
                        lays = book_runner.get("ex", {}).get("availableToLay", [])
                        if backs:
                            best_back = f"{backs[0]['price']} @ {backs[0]['size']}"
                        if lays:
                            best_lay = f"{lays[0]['price']} @ {lays[0]['size']}"

                    print(f"    - {runner_name} (Selection ID: {selection_id}): BACK {best_back}, LAY {best_lay}")

