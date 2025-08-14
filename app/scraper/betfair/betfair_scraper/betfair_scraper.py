from selenium import webdriver
import tempfile
import shutil
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import asyncio
from playwright.async_api import async_playwright
import time

import asyncio

import asyncio

async def dismiss_cookies(page):
    try:
        # Wait for cookie banner container and print its HTML content for debugging
        banner = await page.wait_for_selector('#onetrust-button-group-parent', timeout=15000)
        banner_html = await banner.inner_html()
        print("ℹ️ Cookie banner HTML content:", banner_html[:500])  # print first 500 chars

    except Exception as e:
        print(f"⚠️ Cookie banner container not found: {e}")
        # maybe no banner, or not loaded yet
        # you can still try other methods or return here

    # Check if cookie banner inside an iframe
    iframe_element = await page.query_selector('iframe')
    if iframe_element:
        print("ℹ️ Cookie banner might be inside an iframe, switching context...")
        frame = await iframe_element.content_frame()
        if frame is None:
            print("⚠️ Could not access iframe content.")
            return
        context_page = frame
    else:
        context_page = page

    # Try JS click first (simple & robust if button exists and is clickable)
    try:
        js_result = await context_page.evaluate("""
            () => {
                const btn = document.querySelector('#onetrust-reject-all-handler');
                if (btn && btn.offsetParent !== null) { // visible check
                    btn.click();
                    return true;
                }
                return false;
            }
        """)
        if js_result:
            print("✅ Clicked 'Allow necessary only' button via JS evaluation")
            await asyncio.sleep(2)
            return
        else:
            print("ℹ️ JS click method: button not found or not visible")
    except Exception as e:
        print(f"⚠️ JS click method failed: {e}")

    selectors = [
        ('CSS selector', '#onetrust-reject-all-handler'),
        ('XPath selector', '//button[@id="onetrust-reject-all-handler"]'),
        ('Text selector', 'button:has-text("Allow necessary only")'),
        ('Generic button filtered by text', None),  # handled separately
        ('Wait for function', None)  # handled separately
    ]

    for method, selector in selectors:
        try:
            if method == 'Generic button filtered by text':
                reject_button = context_page.locator('button').filter(has_text='Allow necessary only')
                await reject_button.first.wait_for(timeout=5000)
                await reject_button.first.scroll_into_view_if_needed()
                await reject_button.first.click()
                print(f"✅ Clicked 'Allow necessary only' button using {method}")
                await asyncio.sleep(2)
                return

            elif method == 'Wait for function':
                await context_page.wait_for_function(
                    'document.querySelector("#onetrust-reject-all-handler") !== null && document.querySelector("#onetrust-reject-all-handler").offsetParent !== null',
                    timeout=5000
                )
                reject_button = await context_page.query_selector('#onetrust-reject-all-handler')
                if reject_button:
                    await reject_button.scroll_into_view_if_needed()
                    await reject_button.click()
                    print(f"✅ Clicked 'Allow necessary only' button using {method}")
                    await asyncio.sleep(2)
                    return
                else:
                    print(f"ℹ️ {method}: button not found after wait")

            elif method == 'XPath selector':
                reject_button = await context_page.wait_for_selector(f'xpath={selector}', timeout=5000)
                if reject_button:
                    await reject_button.scroll_into_view_if_needed()
                    await reject_button.click()
                    print(f"✅ Clicked 'Allow necessary only' button using {method}")
                    await asyncio.sleep(2)
                    return
                else:
                    print(f"ℹ️ {method}: button not found")

            else:  # CSS selector or Text selector
                reject_button = await context_page.wait_for_selector(selector, timeout=5000)
                if reject_button:
                    await reject_button.scroll_into_view_if_needed()
                    await reject_button.click()
                    print(f"✅ Clicked 'Allow necessary only' button using {method}")
                    await asyncio.sleep(2)
                    return
                else:
                    print(f"ℹ️ {method}: button not found")

        except Exception as e:
            print(f"⚠️ Failed using {method}: {e}")

    print("❌ Could not find or click the 'Allow necessary only' button by any method.")

async def wait_for_page_stabilize(page, wait_time=2, check_interval=0.2):
    stable_for = 0
    last_scroll_y = await page.evaluate("window.scrollY")
    while stable_for < wait_time:
        await asyncio.sleep(check_interval)
        current_scroll_y = await page.evaluate("window.scrollY")
        if current_scroll_y == last_scroll_y:
            stable_for += check_interval
        else:
            stable_for = 0
            last_scroll_y = current_scroll_y

async def click_stats_tab(page):
    try:
        # Wait for the stats tab button inside modal
        stats_tab = await page.wait_for_selector(
            'xpath=//div[contains(@class, "e367e91883575454-iconButton")]/span[text()="Stats"]', timeout=10000
        )
        await stats_tab.click()
        print("✅ Clicked the 'Stats' tab inside modal")
        await asyncio.sleep(1)  # let content load
    except Exception as e:
        print("⚠️ Could not click Stats tab:", e)

async def scroll_modal_to_bottom(page):
    try:
        # Wait for modal scroll container
        scroll_container = await page.wait_for_selector('#modal-root div[role="dialog"]', timeout=10000)

        last_height = await page.evaluate('(el) => el.scrollHeight', scroll_container)
        while True:
            await page.evaluate('(el) => el.scrollTo(0, el.scrollHeight)', scroll_container)
            await asyncio.sleep(1)  # wait for loading
            new_height = await page.evaluate('(el) => el.scrollHeight', scroll_container)
            if new_height == last_height:
                break
            last_height = new_height
        print("✅ Scrolled modal to bottom to reveal all stats")
    except Exception as e:
        print("⚠️ Could not scroll modal:", e)

async def get_betfair_page_content(url):
    # Create a temporary directory for persistent user data to avoid conflicts
    temp_profile_dir = tempfile.mkdtemp()

    try:
        async with async_playwright() as p:
            # Launch browser with persistent context using temp profile dir (like user-data-dir in Selenium)
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=temp_profile_dir,
                headless=True,
                args=["--no-sandbox"]
            )
            page = await browser_context.new_page()

            await page.goto(url)
            await asyncio.sleep(5)  # Wait for initial scripts

            content = await page.content()
            print(content)

            # Dismiss cookie banner 
            await dismiss_cookies(page)
            print("✅ Hid cookie overlay and banner")


            # Scroll to top and let layout settle
            await page.evaluate("window.scrollTo(0, 0);")
            await asyncio.sleep(2)

            await wait_for_page_stabilize(page, wait_time=3)

            # Click Statistics button
            stats_span = await page.wait_for_selector('xpath=//span[contains(text(), "Statistics")]', timeout=20000)
            stats_button = await stats_span.evaluate_handle('el => el.closest("button")')
            await stats_button.scroll_into_view_if_needed()
            await asyncio.sleep(2)

            try:
                await stats_button.click()
            except Exception:
                await page.evaluate('(el) => el.click()', stats_button)
            print("✅ Clicked Statistics button")


            # await page.wait_for_selector('#modal-root div', timeout=20000)
            await asyncio.sleep(1)

            # Click Stats tab - assuming async click_stats_tab function exists
            await click_stats_tab(page)
            await asyncio.sleep(1)

            # Zoom out page to 80% so all stats fit in modal and no scrolling needed
            await page.evaluate("document.body.style.zoom='80%'")
            await asyncio.sleep(1)

            # Extract page content (modal fully visible, no scroll)
            page_content = await page.content()

            await browser_context.close()

    except Exception as e:
        print("⚠️ Modal could not be opened or processed:", e)
        page_content = None  # or fallback if you want

    finally:
        # Clean up temp profile directory
        shutil.rmtree(temp_profile_dir, ignore_errors=True)

    return page_content



def parse_betfair_match_data(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    data = {}

    # Extract Time
    time_container = soup.find('div', class_='_73836e21fc8d6105-label _73836e21fc8d6105-status')
    data['Time'] = time_container.find('span').text.strip() if time_container and time_container.find('span') else 'N/A'

    # Extract Competition
    comp_tag = soup.find('span', class_='_209611acf0869006-competitionLabel')
    data['Competition'] = comp_tag.text.strip() if comp_tag else 'N/A'

    # Extract Teams robustly
    team_names = []
    for tag in soup.find_all('p'):
        text = tag.text.strip()
        if text and len(text) > 1:
            parent_classes = ' '.join(tag.parent.get('class', [])) if tag.parent else ''
            grandparent_classes = ' '.join(tag.parent.parent.get('class', [])) if tag.parent and tag.parent.parent else ''
            if 'team' in parent_classes.lower() or 'teamname' in parent_classes.lower() or 'team' in grandparent_classes.lower():
                team_names.append(text)
    if len(team_names) >= 2:
        data['Home Team'], data['Away Team'] = team_names[:2]
    else:
        data['Home Team'] = data['Away Team'] = 'N/A'

    # Scores
    score_tags = soup.find_all('div', class_='_90346fd614c6253a-square')
    if len(score_tags) >= 2:
        data['Home Score'] = score_tags[0].text.strip()
        data['Away Score'] = score_tags[1].text.strip()
    else:
        data['Home Score'] = data['Away Score'] = 'N/A'

    # Goals extraction helper
    def extract_goals(container):
        goals = []
        if not container:
            return goals
        goal_divs = container.find_all('div', class_='f9fc9ae5a477983c-container')
        for goal_div in goal_divs:
            minute_span = goal_div.find('span', class_='f9fc9ae5a477983c-minute')
            player_span = goal_div.find('span', class_='f9fc9ae5a477983c-player')
            if minute_span:
                minutes_text = minute_span.text.strip()
                if player_span:
                    goals.append({'Minute': minutes_text, 'Player': player_span.text.strip()})
                else:
                    for m in minutes_text.split(','):
                        m_clean = m.strip()
                        if m_clean:
                            goals.append({'Minute': m_clean, 'Player': None})
        return goals

    home_goals_container = soup.find('div', class_='_150af994cd484669-incidentColumn _150af994cd484669-scoreboardVariantHomeColumn')
    data['Goals'] = {
        'Home': extract_goals(home_goals_container),
        'Away': extract_goals(soup.find('div', class_='_150af994cd484669-incidentColumn _150af994cd484669-scoreboardVariantAwayColumn'))
    }

    data['Stats'] = {}

    # First, extract stats from 'container' divs (other stats except corners)
    stat_containers = soup.find_all('div', class_=lambda c: c and 'container' in c)
    for container in stat_containers:
        label = container.find('span', class_=lambda c: c and 'label' in c)
        if not label:
            continue

        title = label.text.strip().replace('%', '').strip()
        if title in ['Possession', 'Shots On Target', 'Shots Off Target']:
            home_stat = container.find('span', class_=lambda c: c and 'home' in c)
            away_stat = container.find('span', class_=lambda c: c and 'away' in c)
            data['Stats'][title] = {
                'Home': home_stat.text.strip() if home_stat else 'N/A',
                'Away': away_stat.text.strip() if away_stat else 'N/A'
            }

    # Then, extract corners specifically from 'cardStat' divs
    card_stat_divs = soup.find_all('div', class_=lambda c: c and 'cardStat' in c)
    for div in card_stat_divs:
        title_span = div.find('span', class_=lambda c: c and 'title' in c)
        if not title_span:
            continue
        stat_name = title_span.text.strip().capitalize()
        if stat_name == 'Corners':
            home_val = div.find('span', class_=lambda c: c and 'home' in c)
            away_val = div.find('span', class_=lambda c: c and 'away' in c)
            data['Stats'][stat_name] = {
                'Home': home_val.text.strip() if home_val else 'N/A',
                'Away': away_val.text.strip() if away_val else 'N/A'
            }

    return data
