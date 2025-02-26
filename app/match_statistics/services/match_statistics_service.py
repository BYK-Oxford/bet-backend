from sqlalchemy.orm import Session
from app.match_statistics.models.match_statistics_model import MatchStatistics
from app.core.utils import generate_custom_id


class MatchStatisticsService:
    def __init__(self, db: Session):
        self.db = db

    def create_match_statistics(self, match_id: str, statistics_data: dict):
        """Create or update match statistics in the database."""

        # Check if statistics already exist for this match
        existing_stats = self.db.query(MatchStatistics).filter_by(match_id=match_id).first()
        if existing_stats:
            return existing_stats  # Prevent duplicate statistics

        new_id = generate_custom_id(self.db, MatchStatistics, "MS", "match_stat_id")
        match_stats = MatchStatistics(
            match_stat_id=new_id,
            match_id=match_id,
            full_time_home_goals=statistics_data.get("full_time_home_goals", 0),
            full_time_away_goals=statistics_data.get("full_time_away_goals", 0),
            full_time_result=statistics_data.get("full_time_result", ""),
            half_time_home_goals=statistics_data.get("half_time_home_goals", 0),
            half_time_away_goals=statistics_data.get("half_time_away_goals", 0),
            half_time_result=statistics_data.get("half_time_result", ""),
            shots_home=statistics_data.get("shots_home", 0),
            shots_away=statistics_data.get("shots_away", 0),
            shots_on_target_home=statistics_data.get("shots_on_target_home", 0),
            shots_on_target_away=statistics_data.get("shots_on_target_away", 0),
            fouls_home=statistics_data.get("fouls_home", 0),
            fouls_away=statistics_data.get("fouls_away", 0),
            corners_home=statistics_data.get("corners_home", 0),
            corners_away=statistics_data.get("corners_away", 0),
            yellow_cards_home=statistics_data.get("yellow_cards_home", 0),
            yellow_cards_away=statistics_data.get("yellow_cards_away", 0),
            red_cards_home=statistics_data.get("red_cards_home", 0),
            red_cards_away=statistics_data.get("red_cards_away", 0),
        )

        self.db.add(match_stats)
        self.db.commit()
        self.db.refresh(match_stats)
        return match_stats
