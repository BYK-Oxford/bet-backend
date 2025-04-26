from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

def get_fishy_page_content_selenium(url):
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode (without UI)
    options.add_argument("--no-sandbox")  # Needed for Render (and other headless environments)
    options.add_argument("--disable-dev-shm-usage")  # Disable shared memory usage
    options.add_argument("--disable-gpu")  # Disable GPU (not needed in headless mode)
    options.add_argument("--disable-features=VizDisplayCompositor")  # Avoid possible crashes on headless
    options.add_argument("window-size=1920x1080")
    
    # Set path to Chromium binary (installed on Render)
    options.binary_location = "/usr/bin/chromium"  # Path to Chromium installed on Render

    
    service = Service("app/chromedriver-linux64/chromedriver")  # Path to ChromeDriver

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(5)  # Wait for the page to load (you may want to adjust this)
    
    page_content = driver.page_source
    driver.quit()  # Close the browser after fetching the page
    
    return page_content

def parse_fishy_league_standing_data(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    standings_data = []
    
    # Extract year from caption and format it
    caption = soup.find('caption')
    if caption:
        year_text = caption.text.strip().split()[0]  # Extract the first part (year)
        formatted_year = year_text.replace('-', '/')  # Convert to yyyy/yyyy format
    else:
        formatted_year = "Unknown"
    
    rows = soup.find_all('tr', class_='cats2')
    found_first_table = False  # To track if we have already processed a table

    for row in rows:
        cols = row.find_all('td')

        if len(cols) >= 19:
            position = cols[0].text.strip()

            # Start collecting data when we first encounter position "1"
            if position == "1":
                if found_first_table:
                    break  # Stop when we see "1" again (new table detected)
                found_first_table = True  # Mark that we've found the first table
            
            if found_first_table:
                team_name = cols[1].find('a').text.strip()
                played = cols[2].text.strip()
                wins = cols[13].text.strip()
                draws = cols[14].text.strip()
                losses = cols[15].text.strip()
                goals_for = cols[16].text.strip()
                goals_against = cols[17].text.strip()
                goal_difference = cols[18].text.strip()
                points = cols[19].text.strip()

                standings_data.append({
                    'Year': formatted_year,
                    'Position': position,
                    'Team': team_name,
                    'Played': played,
                    'Wins': wins,
                    'Draws': draws,
                    'Losses': losses,
                    'Goals For': goals_for,
                    'Goals Against': goals_against,
                    'Goal Difference': goal_difference,
                    'Points': points
                })

    return standings_data
