import json
from sqlalchemy.orm import Session
from app.teams.models import Team
from app.leagues.services.league_service import LeagueService
from app.teams.services.team_alias_service import TeamAliasService
from app.core.utils import generate_custom_id

class TeamService:
    def __init__(self, db: Session):
        self.db = db
        self.league_service = LeagueService(db)
        self.alias_service = TeamAliasService(db)

        # Load aliases from JSON file
        with open("./app/teams/teams_aliases.json", "r") as f:
            self.alias_mapping = json.load(f)

    def get_or_create_team(self, team_name: str, league_name: str):
        """Retrieve or create a team, ensuring aliases are handled correctly."""

        # Step 1: Check if the team name exists in TeamAlias table
        alias_entry = self.alias_service.get_team_by_alias(team_name)
        if alias_entry:
            return alias_entry  # Return the official team

        # Step 2: Check if the team already exists in the Team table
        team = self.db.query(Team).filter(Team.team_name == team_name).first()
        if team:
            return team  # Team already exists, return it

        # Step 3: Determine if the team name is an alias of another team
        official_team_name = None
        for real_name, aliases in self.alias_mapping.items():
            if team_name in aliases:
                official_team_name = real_name
                break

        # Step 4: If it's an alias, link it to the official team
        if official_team_name:
            team = self.db.query(Team).filter(Team.team_name == official_team_name).first()
            if team:
                self.alias_service.get_or_create_alias(team.team_id, team_name)
                return team  # Return the official team

        # Step 5: If the team is entirely new, create it and store alias
        league = self.league_service.get_or_create_league(league_name)

        # At this point, the league service will handle country creation automatically
        new_id = generate_custom_id(self.db, Team, "T", "team_id")

        new_team = Team(
            team_id=new_id,
            team_name=team_name,
            league_id=league.league_id,
            country_id=league.country_id  # Country is now managed by LeagueService
        )
        self.db.add(new_team)
        self.db.commit()
        self.db.refresh(new_team)

        # Step 6: Save this new team name as its own alias
        self.alias_service.get_or_create_alias(new_team.team_id, team_name)

        return new_team
