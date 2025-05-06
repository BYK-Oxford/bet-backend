import requests
import time

urls = [
    "https://bet-backend-1.onrender.com/odds/scrape-new-odds/",
    "https://bet-backend-1.onrender.com/current-league/scrape-current-league/",
    "https://bet-backend-1.onrender.com/odds-calculation/calculate-ratios/",
]

# Iterate through the URLs and make sure they are hit sequentially
for idx, url in enumerate(urls):
    try:
        print(f"Starting request {idx + 1}: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f"Success: {url} -> {response.status_code}")
        else:
            print(f"Failed: {url} -> Status code: {response.status_code}")
            break  # Stop if any request fails, or handle accordingly (retry, etc.)

    except Exception as e:
        print(f"Error: {url} -> {e}")
        break  # Stop if there is an exception
    time.sleep(2)  # Optional: wait a few seconds before proceeding to the next one
