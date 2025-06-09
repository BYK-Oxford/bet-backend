# core/betfair_api_client.py

import json
import urllib.request
import urllib.error

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
