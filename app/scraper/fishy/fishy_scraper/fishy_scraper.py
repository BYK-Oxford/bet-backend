from playwright.async_api import async_playwright
import asyncio
import os
from bs4 import BeautifulSoup

async def get_fishy_page_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]  # Add this if running inside Docker
        )
        page = await browser.new_page()
        await page.goto(url)
        await asyncio.sleep(5)  # Wait for the page to load
        page_content = await page.content()
        await browser.close()
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
