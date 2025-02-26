from sqlalchemy.orm import Session
from app.standings.models.standings_model import Standing
from app.teams.services.team_service import TeamService
from app.leagues.services.league_service import LeagueService
from app.seasons.services.season_service import SeasonService

class StandingService:
    def __init__(self, db: Session):
        self.db = db
        self.team_service = TeamService(db)
        self.league_service = LeagueService(db)
        self.season_service = SeasonService(db)

    def create_standing(self, standing_data: dict):
        """Create or update a standing record in the database."""
        
        # Get or create related entities
        league = self.league_service.get_or_create_league(standing_data["league"])
        season = self.season_service.get_or_create_season(standing_data["season"])
        team = self.team_service.get_or_create_team(standing_data["team"], standing_data["league"])

        # Check for existing standing
        existing_standing = (
            self.db.query(Standing)
            .filter(
                Standing.team_id == team.team_id,
                Standing.league_id == league.league_id,
                Standing.season_id == season.season_id
            )
            .first()
        )

        if existing_standing:
            # Update only non-FK fields
            update_fields = [
                "position", "played", "wins", "draws", "losses",
                "goals_for", "goals_against", "goal_difference", "points"
            ]
            for key in update_fields:
                if key in standing_data:
                    setattr(existing_standing, key, standing_data[key])
            self.db.commit()
            self.db.refresh(existing_standing)
            return existing_standing

        # Create new standing
        standing = Standing(
            standing_id=standing_data["standing_id"],
            team_id=team.team_id,     
            league_id=league.league_id,  
            season_id=season.season_id, 
            position=standing_data["position"],
            played=standing_data["played"],
            wins=standing_data["wins"],
            draws=standing_data["draws"],
            losses=standing_data["losses"],
            goals_for=standing_data["goals_for"],
            goals_against=standing_data["goals_against"],
            goal_difference=standing_data["goal_difference"],
            points=standing_data["points"]
        )

        self.db.add(standing)
        self.db.commit()
        self.db.refresh(standing)
        return standing
