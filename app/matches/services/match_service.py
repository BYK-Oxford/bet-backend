from sqlalchemy.orm import Session
from datetime import datetime
from app.matches.models import Match
from app.leagues.services.league_service import LeagueService
from app.seasons.services.season_service import SeasonService
from app.teams.services.team_service import TeamService
from app.referee.services.referee_service import RefereeService
from app.core.utils import generate_custom_id

class MatchService:
    def __init__(self, db: Session):
        self.db = db
        self.league_service = LeagueService(db)
        self.season_service = SeasonService(db)
        self.team_service = TeamService(db)
        self.referee_service = RefereeService(db)
    

    def create_match(self, match_data: dict):
        """Create or update a match record in the database."""
        league = self.league_service.get_or_create_league(match_data["league"])
        season = self.season_service.get_or_create_season(match_data["season"])
        home_team = self.team_service.get_or_create_team(match_data["home_team"], match_data["league"])
        away_team = self.team_service.get_or_create_team(match_data["away_team"], match_data["league"])
        referee = self.referee_service.get_or_create_referee(match_data["referee"])


         # Check for existing match
        existing_match = (
            self.db.query(Match)
            .filter(
                Match.date == datetime.strptime(match_data["date"], "%d/%m/%Y %H:%M"),
                Match.home_team_id == home_team.team_id,
                Match.away_team_id == away_team.team_id
            )
            .first()
        )

        if existing_match:
            return existing_match  # Prevent duplicate insertion
        
        new_id = generate_custom_id(self.db, Match, "M", "match_id")

        match = Match(
            match_id=match_data["match_id"],
            date=datetime.strptime(match_data["date"],  "%d/%m/%Y %H:%M"),
            league_id=league.league_id,
            season_id=season.season_id,
            home_team_id=home_team.team_id,
            away_team_id=away_team.team_id,
            referee_id=referee.ref_id
        )

        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)

     
        return match