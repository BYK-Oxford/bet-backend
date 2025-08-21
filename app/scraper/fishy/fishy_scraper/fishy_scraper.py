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
        await asyncio.sleep(10)  # Wait for the page to load
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
    manual_position = 1
    found_first_table = False

    for row in rows:
        cols = row.find_all('td')

        if len(cols) >= 20:
            pos_text = cols[0].text.strip()

            # Inject position manually if missing
            if pos_text == "":
                position = str(manual_position)
                manual_position += 1
            else:
                position = pos_text
                manual_position = int(position) + 1  # Reset counter in case HTML has real numbers

            # Start on first table only
            if position == "1":
                if found_first_table:
                    break  # New table starts, stop collecting
                found_first_table = True

            if found_first_table:
                try:
                    team_name = cols[1].find('a').text.strip()
                except AttributeError:
                    continue  # Skip if team name link not found

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
