from sqlalchemy.orm import Session
from typing import List, Dict, Any
from itertools import combinations
from app.odds_calculation.services.odds_retrieval_service import OddsRetrievalService

class OddsProcessorService:
    def __init__(self, db: Session):
        self.db = db

    def process_calculated_odds(self) -> List[Dict[str, Any]]:
        """
        Retrieves all upcoming calculated odds with team, league, and odds details.
        """
        retrieval_service = OddsRetrievalService(self.db)
        calculated_odds = retrieval_service.get_all_calculated_odds(include_market_data=True)
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

    def find_value_for_money_sets(self, set_size=3, num_sets=3):
        """
        Find 'num_sets' sets of 'set_size' value-for-money matches.
        Each set contains unique matches (no overlap across sets).
        Only matches with selected odds ≥ set_size are used (e.g. ≥3.0 for set of 3).
        Returns a list of sets (each is a list of match dicts).
        """
        matches = self.get_value_for_money_matches()
        v4m_candidates = []

        for match in matches:
            best_option = None

            try:
                home_odds = match.get("home_odds")
                draw_odds = match.get("draw_odds")
                away_odds = match.get("away_odds")

                calc_home = match.get("calculated_home_chance", 0) * 100
                calc_draw = match.get("calculated_draw_chance", 0) * 100
                calc_away = match.get("calculated_away_chance", 0) * 100

                prob_total = (1 / home_odds) + (1 / draw_odds) + (1 / away_odds)
                bookmaker_home_pct = (1 / home_odds) / prob_total * 100
                bookmaker_draw_pct = (1 / draw_odds) / prob_total * 100
                bookmaker_away_pct = (1 / away_odds) / prob_total * 100

                diff_home = calc_home - bookmaker_home_pct
                diff_draw = calc_draw - bookmaker_draw_pct
                diff_away = calc_away - bookmaker_away_pct

                options = [
                    {"side": "home", "odds": home_odds, "diff": diff_home},
                    {"side": "draw", "odds": draw_odds, "diff": diff_draw},
                    {"side": "away", "odds": away_odds, "diff": diff_away},
                ]

                valid_options = [opt for opt in options if opt["odds"] >= set_size and opt["diff"] > 0]
                if valid_options:
                    best_option = max(valid_options, key=lambda x: x["diff"])

                if best_option:
                    match_copy = match.copy()
                    match_copy["selected_outcome"] = best_option["side"]
                    match_copy["selected_odds"] = best_option["odds"]
                    match_copy["value_diff"] = best_option["diff"]
                    v4m_candidates.append(match_copy)

            except (ZeroDivisionError, TypeError):
                continue

        # Generate all possible valid combinations
        all_valid_sets = []
        for match_set in combinations(v4m_candidates, set_size):
            match_ids = [m.get("odds_calculation_id") for m in match_set]
            if len(set(match_ids)) == set_size:  # Ensure all match IDs are unique within the set
                total_diff = sum(m["value_diff"] for m in match_set)
                all_valid_sets.append((total_diff, match_set))

        # Sort by total value diff descending
        all_valid_sets.sort(key=lambda x: x[0], reverse=True)

        # Pick top 'num_sets' sets with no overlapping matches
        selected_sets = []
        used_match_ids = set()

        for _, match_set in all_valid_sets:
            current_ids = {m.get("odds_calculation_id") for m in match_set}
            if used_match_ids.isdisjoint(current_ids):
                selected_sets.append(list(match_set))
                used_match_ids.update(current_ids)
            if len(selected_sets) == num_sets:
                break

        return selected_sets
