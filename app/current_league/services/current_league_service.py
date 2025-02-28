from sqlalchemy.orm import Session
from app.current_league.models.current_league_model import CurrentLeague
from app.teams.services.team_service import TeamService
from app.leagues.services.league_service import LeagueService
from app.seasons.services.season_service import SeasonService
from app.core.utils import generate_custom_id

class CurrentLeagueService:
    def __init__(self, db: Session):
        self.db = db
        self.team_service = TeamService(db)
        self.league_service = LeagueService(db)
        self.season_service = SeasonService(db)

    def create_current_league(self, league_data: dict):
        """Create or update current league standing data in the database."""
        
        # Get or create related entities using their respective services
        team = self.team_service.get_or_create_team(league_data.get("team_id"), league_data.get("league_code"))
        league = self.league_service.get_or_create_league(league_data.get("league_code"))
        season = self.season_service.get_or_create_season(league_data.get("year"))
        
        # Check if standing already exists for this team in this league and season
        existing_standing = self.db.query(CurrentLeague).filter(
            CurrentLeague.team_id == team.team_id,
            CurrentLeague.league_id == league.league_id,
            CurrentLeague.season_id == season.season_id
        ).first()
        
        if existing_standing:
            # Update existing standing with new data
            existing_standing.position = league_data.get("position")
            existing_standing.played = league_data.get("played")
            existing_standing.wins = league_data.get("wins")
            existing_standing.draws = league_data.get("draws")
            existing_standing.losses = league_data.get("losses")
            existing_standing.goals_for = league_data.get("goals_for")
            existing_standing.goals_against = league_data.get("goals_against")
            existing_standing.goal_difference = league_data.get("goal_difference")
            existing_standing.points = league_data.get("points")
            
            self.db.commit()
            self.db.refresh(existing_standing)
            return existing_standing

        new_id = generate_custom_id(self.db, CurrentLeague, "CL", "current_league_id")

        # Create a new CurrentLeague instance
        new_standing = CurrentLeague(
            current_league_id=new_id,
            team_id=team.team_id,
            league_id=league.league_id,
            season_id=season.season_id,
            position=league_data.get("position"),
            played=league_data.get("played"),
            wins=league_data.get("wins"),
            draws=league_data.get("draws"),
            losses=league_data.get("losses"),
            goals_for=league_data.get("goals_for"),
            goals_against=league_data.get("goals_against"),
            goal_difference=league_data.get("goal_difference"),
            points=league_data.get("points")
        )

        # Add the new standing to the session and commit the transaction
        self.db.add(new_standing)
        self.db.commit()
        self.db.refresh(new_standing)
        
        return new_standing
