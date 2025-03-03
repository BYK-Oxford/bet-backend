from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta


# Function to fetch the page content using Selenium (for dynamic content)
def get_page_content_selenium(url):
    options = Options()
    options.headless = True  # Run Chrome in headless mode (without UI)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    time.sleep(5)  # Wait for the page to load (adjust this sleep if needed)

    page_content = driver.page_source
    driver.quit()  # Close the browser after fetching the page

    return page_content

def convert_fraction_to_decimal(fractional_odds):
    # Check if the input contains '/' which indicates a fraction
    if '/' in fractional_odds:
        try:
            numerator, denominator = map(int, fractional_odds.split('/'))
            decimal_odds = (numerator / denominator) + 1
            return round(decimal_odds, 2)  # Round to 2 decimal places
        except ValueError:
            return fractional_odds  # Return original value if conversion fails
    return fractional_odds  # Return original value if not a fraction

def convert_relative_date(date_str):
    """Convert relative dates to proper date format."""
    today = datetime.now()
    
    if date_str.startswith('Today'):
        return today.strftime('%d %b %Y')
    elif date_str.startswith('Tomorrow'):
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime('%d %b %Y')
    else:
        # For other dates, try to parse the date
        try:
            # Extract the date part after the comma if it exists
            if ',' in date_str:
                date_str = date_str.split(',')[1].strip()
            
            # First try to parse with year if it's included
            try:
                return datetime.strptime(date_str, '%d %b %Y').strftime('%d %b %Y')
            except ValueError:
                # If no year in the string, add the current year
                date_str = f"{date_str} {today.year}"
                return datetime.strptime(date_str, '%d %b %Y').strftime('%d %b %Y')
        except ValueError:
            return date_str

def parse_match_data(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    match_data = []
    current_date = None
    seen_matches = set()  # Track seen matches to avoid duplicates

    for element in soup.find_all('div', class_=['border-black-borders', 'flex', 'w-full', 'min-w-0']):
        # Check if the element is a date header
        date_div = element.find('div', class_='text-black-main font-main w-full truncate text-xs font-normal leading-5')
        if date_div:
            raw_date = date_div.text.strip()
            current_date = convert_relative_date(raw_date)  # Convert the date format
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
