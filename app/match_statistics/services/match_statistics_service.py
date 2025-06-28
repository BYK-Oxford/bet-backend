from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.orm import aliased
from app.match_statistics.models.match_statistics_model import MatchStatistics
from app.core.utils import generate_custom_id
from datetime import datetime
from sqlalchemy.orm import joinedload
from app.matches.models.match_model import Match
from app.teams.models.team_model import Team
from app.leagues.models.leagues_models import League
from app.country.models.country_model import Country
from app.odds_calculation.models.odds_calculation_model import OddsCalculation 


class MatchStatisticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_match_statistics(self):
        """Fetch all match statistics from the match_statistics table."""
        match_statistics = self.db.query(MatchStatistics).limit(3).all()
        return match_statistics

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


    def get_historic_matches_between_teams(self, odds_calculation_id: str):
        """Fetch all past matches where home team played as home and away team played as away against each other."""

        from sqlalchemy.orm import aliased

        # Step 1: Fetch the OddsCalculation object
        odds_calculation = (
            self.db.query(OddsCalculation)
            .filter_by(odds_calculation_id=odds_calculation_id)
            .first()
        )

        if not odds_calculation:
            raise HTTPException(status_code=404, detail="Odds calculation not found")

        home_team_id = odds_calculation.home_team_id
        away_team_id = odds_calculation.away_team_id

        # Aliases for team joins
        HomeTeam = aliased(Team)
        AwayTeam = aliased(Team)

        # Step 2: Query matches with same home/away teams and join MatchStatistics + Team aliases
        results = (
            self.db.query(
                Match.match_id,
                Match.date,
                Match.home_team_id,
                Match.away_team_id,
                HomeTeam.team_name.label("home_team_name"),
                HomeTeam.home_primary_color,
                HomeTeam.home_secondary_color,
                AwayTeam.team_name.label("away_team_name"),
                AwayTeam.away_primary_color,
                AwayTeam.away_secondary_color,
                MatchStatistics.full_time_home_goals,
                MatchStatistics.full_time_away_goals,
                MatchStatistics.full_time_result,
                MatchStatistics.half_time_home_goals,
                MatchStatistics.half_time_away_goals,
                MatchStatistics.half_time_result,
                MatchStatistics.shots_home,
                MatchStatistics.shots_away,
                MatchStatistics.shots_on_target_home,
                MatchStatistics.shots_on_target_away,
                MatchStatistics.fouls_home,
                MatchStatistics.fouls_away,
                MatchStatistics.corners_home,
                MatchStatistics.corners_away,
                MatchStatistics.yellow_cards_home,
                MatchStatistics.yellow_cards_away,
                MatchStatistics.red_cards_home,
                MatchStatistics.red_cards_away,
            )
            .join(MatchStatistics, Match.match_id == MatchStatistics.match_id)
            .join(HomeTeam, Match.home_team_id == HomeTeam.team_id)
            .join(AwayTeam, Match.away_team_id == AwayTeam.team_id)
            .filter(Match.home_team_id == home_team_id)
            .filter(Match.away_team_id == away_team_id)
            .order_by(Match.date.desc())
            .all()
        )

        if not results:
            return {"message": "No historic match data found for the given odds calculation."}

        # Step 3: Format the response
        historic_matches = []
        for row in results:
            match = {
                "match_id": row.match_id,
                "date": row.date,
                "home_team_id": row.home_team_id,
                "away_team_id": row.away_team_id,
                "home_team_name": row.home_team_name,
                "away_team_name": row.away_team_name,
                "home_primary_color": row.home_primary_color,
                "home_secondary_color": row.home_secondary_color,
                "away_primary_color": row.away_primary_color,
                "away_secondary_color": row.away_secondary_color,
                "statistics": {
                    "full_time_home_goals": row.full_time_home_goals,
                    "full_time_away_goals": row.full_time_away_goals,
                    "full_time_result": row.full_time_result,
                    "half_time_home_goals": row.half_time_home_goals,
                    "half_time_away_goals": row.half_time_away_goals,
                    "half_time_result": row.half_time_result,
                    "shots_home": row.shots_home,
                    "shots_away": row.shots_away,
                    "shots_on_target_home": row.shots_on_target_home,
                    "shots_on_target_away": row.shots_on_target_away,
                    "fouls_home": row.fouls_home,
                    "fouls_away": row.fouls_away,
                    "corners_home": row.corners_home,
                    "corners_away": row.corners_away,
                    "yellow_cards_home": row.yellow_cards_home,
                    "yellow_cards_away": row.yellow_cards_away,
                    "red_cards_home": row.red_cards_home,
                    "red_cards_away": row.red_cards_away,
                }
            }
            historic_matches.append(match)

        return historic_matches
