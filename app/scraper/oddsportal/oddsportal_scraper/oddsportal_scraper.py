import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time


# Function to fetch the page content using Selenium (for dynamic content)
def get_page_content_selenium(url):
    options = Options()
    options.headless = True  # Run Chrome in headless mode (without UI)
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(5)  # Wait for the page to load (adjust this sleep if needed)

    page_content = driver.page_source
    driver.quit()  # Close the browser after fetching the page

    return page_content

def convert_fraction_to_decimal(fractional_odds):
    try:
        numerator, denominator = map(int, fractional_odds.split('/'))
        decimal_odds = (numerator / denominator) + 1
        return round(decimal_odds, 2)  # Round to 2 decimal places
    except ValueError:
        return 'N/A'  # Return 'N/A' if the odds are not in fractional form


def parse_match_data(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    match_data = []
    current_date = None
    seen_matches = set()  # Track seen matches to avoid duplicates

    for element in soup.find_all('div', class_=['border-black-borders', 'flex', 'w-full', 'min-w-0']):
        # Check if the element is a date header
        date_div = element.find('div', class_='text-black-main font-main w-full truncate text-xs font-normal leading-5')
        if date_div:
            current_date = date_div.text.strip()
            continue

        # Process match details
        match = element.find_parent('div', class_='group flex')
        if match:
            match_time = match.find('p').text.strip()
            home_team = match.find('a', title=True).find('p', class_='participant-name').text.strip()
            away_team = match.find_all('a', title=True)[1].find('p', class_='participant-name').text.strip()

            odds_divs = match.find_all('p', class_='height-content')
            home_odds, draw_odds, away_odds = 'N/A', 'N/A', 'N/A'
            if len(odds_divs) == 3:
                 # Extract fractional odds and convert to decimal
                home_odds = convert_fraction_to_decimal(odds_divs[0].text.strip())
                draw_odds = convert_fraction_to_decimal(odds_divs[1].text.strip())
                away_odds = convert_fraction_to_decimal(odds_divs[2].text.strip())


            # Create a unique identifier for each match
            match_id = (current_date, match_time, home_team, away_team)

            # Avoid adding duplicate matches
            if match_id not in seen_matches:
                seen_matches.add(match_id)
                match_data.append({
                    'Date': current_date,
                    'Time': match_time,
                    'Home Team': home_team,
                    'Away Team': away_team,
                    'Home Odds': home_odds,
                    'Draw Odds': draw_odds,
                    'Away Odds': away_odds
                })

    return match_data
