from playwright.sync_api import sync_playwright
import json
import time


class SofaScoreService:
    LIVE_API_URL = "https://api.sofascore.com/api/v1/sport/football/events/live"
    STATS_API_URL = "https://api.sofascore.com/api/v1/event/{id}/statistics"
    SELECTED_LEAGUES = [
        "Premier League", "Championship",
        "LaLiga", "LaLiga 2",
        "Bundesliga", "2. Bundesliga",
        "Serie A", "Serie B",
        "Ligue 1",
        "Scottish Premiership", "Scottish Championship",
        "Trendyol Süper Lig"
    ]

    def __init__(self, headless: bool = True):
        self.headless = headless

    def _game_clock(self, start_ts, status_desc, injury_time1=None, injury_time2=None):
        """
        Calculates the current match minute based on the start timestamp and match status.
        """
        now = int(time.time())  # current Unix timestamp
        desc = (status_desc or "").lower()

        if "1st" in desc:
            minute = (now - start_ts) // 60
            if injury_time1 and minute > 45:
                return f"45+{minute - 45}"
            return minute

        elif "half" in desc and "time" in desc:
            return 45

        elif "2nd" in desc:
            minute = 45 + ((now - start_ts) // 60)
            if injury_time2 and minute > 90:
                return f"90+{minute - 90}"
            return minute

        elif "extra time" in desc:
            minute = ((now - start_ts) // 60)
            return f"{minute} ET"

        return None

    def _extract_required_stats(self, stats_json):
        """
        Extracts home/away shots on target, shots off target, and corner kicks.
        """
        stats_result = {
            "homeShotsOnTarget": None,
            "awayShotsOnTarget": None,
            "homeShotsOffTarget": None,
            "awayShotsOffTarget": None,
            "cornerKicksHome": None,
            "cornerKicksAway": None
        }
        try:
            groups = stats_json["statistics"][0]["groups"]
            for group in groups:
                for item in group["statisticsItems"]:
                    key = item.get("key")
                    if key == "shotsOnGoal":
                        stats_result["homeShotsOnTarget"] = item.get("homeValue")
                        stats_result["awayShotsOnTarget"] = item.get("awayValue")
                    elif key == "shotsOffGoal":
                        stats_result["homeShotsOffTarget"] = item.get("homeValue")
                        stats_result["awayShotsOffTarget"] = item.get("awayValue")
                    elif key == "cornerKicks":
                        stats_result["cornerKicksHome"] = item.get("homeValue")
                        stats_result["cornerKicksAway"] = item.get("awayValue")
        except (KeyError, IndexError):
            pass
        return stats_result

    def get_live_matches(self):
        """
        Fetches live match data for selected leagues, including statistics.
        Returns a list of dictionaries with match details.
        """
        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            try:
                context = browser.new_context()
                page = context.new_page()

                # Get live events
                page.goto(self.LIVE_API_URL)
                try:
                    data = json.loads(page.inner_text("pre"))
                except json.JSONDecodeError:
                    browser.close()
                    raise ValueError("Failed to parse JSON from live events.")

                if "events" not in data:
                    browser.close()
                    raise ValueError("No 'events' found in live data.")

                # Loop through events
                for event in data["events"]:
                    league_name = event.get("tournament", {}).get("name")
                    if league_name not in self.SELECTED_LEAGUES:
                        continue

                    match_data = {
                        "startTimestamp": event.get("startTimestamp"),
                        "status.timestamp": event.get("statusTime", {}).get("timestamp"),
                        "id": event.get("id"),
                        "currentMinute": self._game_clock(
                            event.get("time", {}).get("currentPeriodStartTimestamp"),
                            event.get("status", {}).get("description")
                        ),
                        "changeTimestamp": event.get("changes", {}).get("changeTimestamp"),
                        "currentPeriodStartTimestamp": event.get("time", {}).get("currentPeriodStartTimestamp"),
                        "homeScore.current": event.get("homeScore", {}).get("current"),
                        "homeScore.period1": event.get("homeScore", {}).get("period1"),
                        "homeScore.period2": event.get("homeScore", {}).get("period2"),
                        "awayScore.current": event.get("awayScore", {}).get("current"),
                        "awayScore.period1": event.get("awayScore", {}).get("period1"),
                        "awayScore.period2": event.get("awayScore", {}).get("period2"),
                        "homeTeam.name": event.get("homeTeam", {}).get("name"),
                        "awayTeam.name": event.get("awayTeam", {}).get("name"),
                        "lastPeriod": event.get("lastPeriod"),
                        "finalResultOnly": event.get("finalResultOnly"),
                        "status.description": event.get("status", {}).get("description"),
                        "status.type": event.get("status", {}).get("type"),
                        "customId": event.get("customId"),
                        "slug": event.get("slug")
                    }

                    # Fetch match statistics
                    stats_url = self.STATS_API_URL.format(id=event.get("id"))
                    page.goto(stats_url)
                    try:
                        stats_content = json.loads(page.inner_text("pre"))
                        match_data.update(self._extract_required_stats(stats_content))
                    except Exception as e:
                        match_data["statsError"] = f"Could not fetch stats: {e}"

                    results.append(match_data)

            finally:
                browser.close()

        return results
