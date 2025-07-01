from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.odds_calculation.services.odds_retrieval_service import OddsRetrievalService

class OddsProcessorService:
    def __init__(self, db: Session):
        self.db = db

    def process_calculated_odds(self) -> List[Dict[str, Any]]:
        """
        Retrieves all upcoming calculated odds with team, league, and odds details.
        """
        retrieval_service = OddsRetrievalService(self.db)
        calculated_odds = retrieval_service.get_all_calculated_odds()
        return calculated_odds

    def get_value_for_money_matches(self) -> List[Dict[str, Any]]:
        """
        Filters and ranks matches based on the 'value for money' principle.
        Returns top 13 matches with maximum positive arbitrage difference.
        """
        matches = self.process_calculated_odds()
        v4m_matches = []

        for match in matches:
            home_odds = match.get("home_odds")
            draw_odds = match.get("draw_odds")
            away_odds = match.get("away_odds")

            # Skip if any odds are missing or zero
            if not all([home_odds, draw_odds, away_odds]):
                continue

            try:
                # Bookmaker implied total probability
                prob_total = (1 / home_odds) + (1 / draw_odds) + (1 / away_odds)

                bookmaker_home_pct = (1 / home_odds) / prob_total
                bookmaker_draw_pct = (1 / draw_odds) / prob_total
                bookmaker_away_pct = (1 / away_odds) / prob_total

                # Calculate percentage differences
                diff_home = (match["calculated_home_chance"] * 100) - (bookmaker_home_pct * 100)
                diff_draw = (match["calculated_draw_chance"] * 100) - (bookmaker_draw_pct * 100)
                diff_away = (match["calculated_away_chance"] * 100) - (bookmaker_away_pct * 100)

                max_diff = max(diff_home, diff_draw, diff_away)

                if max_diff > 7.5:
                    match_copy = match.copy()
                    match_copy["diff_home"] = diff_home
                    match_copy["diff_draw"] = diff_draw
                    match_copy["diff_away"] = diff_away
                    match_copy["max_diff"] = max_diff
                    v4m_matches.append(match_copy)

            except (ZeroDivisionError, TypeError):
                # Log or handle bad data gracefully
                continue

        # Sort descending by max_diff (value opportunity)
        sorted_matches = sorted(v4m_matches, key=lambda x: x["max_diff"], reverse=True)

        # Return top 13
        return sorted_matches
