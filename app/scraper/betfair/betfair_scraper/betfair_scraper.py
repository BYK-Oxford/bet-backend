from selenium import webdriver
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
import time


def dismiss_cookies(driver):
    wait = WebDriverWait(driver, 10)
    try:
        reject_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-reject-all-handler')))
        reject_button.click()
        print("✅ Clicked 'Allow necessary only' button (reject all cookies)")
        time.sleep(2)
    except TimeoutException:
        print("ℹ️ No cookie reject button found or banner already dismissed")

def wait_for_page_stabilize(driver, wait_time=2, check_interval=0.2):
    last_scroll_y = driver.execute_script("return window.scrollY;")
    stable_for = 0
    while stable_for < wait_time:
        time.sleep(check_interval)
        current_scroll_y = driver.execute_script("return window.scrollY;")
        if current_scroll_y == last_scroll_y:
            stable_for += check_interval
        else:
            stable_for = 0
            last_scroll_y = current_scroll_y

def click_stats_tab(driver):
    wait = WebDriverWait(driver, 10)
    try:
        stats_tab = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            '//div[contains(@class, "e367e91883575454-iconButton")]/span[text()="Stats"]'
        )))
        stats_tab.click()
        print("✅ Clicked the 'Stats' tab inside modal")
        time.sleep(1)  # let content load
    except Exception as e:
        print("⚠️ Could not click Stats tab:", e)

def scroll_modal_to_bottom(driver):
    wait = WebDriverWait(driver, 10)
    try:
        # Find the modal scroll container (adjust selector if needed)
        scroll_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#modal-root div[role="dialog"]')))
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
        while True:
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_container)
            time.sleep(1)  # wait for loading
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
            if new_height == last_height:
                break
            last_height = new_height
        print("✅ Scrolled modal to bottom to reveal all stats")
    except Exception as e:
        print("⚠️ Could not scroll modal:", e)

def get_betfair_page_content_selenium(url):
    options = Options()
    options.headless = False  # To actually see resizing in action, headless False is better for debugging
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    try:
        time.sleep(5)  # Wait for initial scripts

        # Dismiss cookie banner
        dismiss_cookies(driver)

        # Scroll to top and let layout settle
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        wait_for_page_stabilize(driver, wait_time=3)

        # Click Statistics button
        stats_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Statistics")]')))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", stats_button)
        time.sleep(2)

        try:
            stats_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", stats_button)
        print("✅ Clicked Statistics button")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#modal-root div')))
        time.sleep(1)

        # Click Stats tab
        click_stats_tab(driver)
        time.sleep(1)

        # *** NEW: Zoom out page to 80% so all stats fit in modal and no scrolling needed ***
        driver.execute_script("document.body.style.zoom='80%';")
        time.sleep(1)  # allow layout to adjust

        # Now extract page content (modal fully visible, no scroll)
        page_content = driver.page_source

    except Exception as e:
        print("⚠️ Modal could not be opened or processed:", e)
        page_content = driver.page_source

    driver.quit()
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
