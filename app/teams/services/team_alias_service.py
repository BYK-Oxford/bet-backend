from sqlalchemy.orm import Session
from app.teams.models import TeamAlias, Team
from app.core.utils import generate_custom_id

class TeamAliasService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_alias(self, team_id: str, alias_name: str):
        """Retrieve an alias for a team or create a new one."""
        
        # ✅ First, ensure the team exists
        team = self.db.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            raise ValueError(f"Team with ID {team_id} does not exist. Cannot create alias.")

        # ✅ Check if alias already exists
        alias = self.db.query(TeamAlias).filter(TeamAlias.alias_name == alias_name, TeamAlias.team_id == team_id).first()

        if not alias:
            # Generate unique alias_id (TA1, TA2, etc.)
            new_id = generate_custom_id(self.db, TeamAlias, "TA", "alias_id")

            alias = TeamAlias(alias_id=new_id, alias_name=alias_name, team_id=team_id)
            self.db.add(alias)
            self.db.commit()
            self.db.refresh(alias)

        return alias

    def get_aliases_by_team(self, team_id: str):
        """Retrieve all aliases for a given team."""
        return self.db.query(TeamAlias).filter(TeamAlias.team_id == team_id).all()

    def get_team_by_alias(self, alias_name: str):
        """Retrieve the team associated with a given alias."""
        alias = self.db.query(TeamAlias).filter(TeamAlias.alias_name == alias_name).first()
        if alias:
            return self.db.query(Team).filter(Team.team_id == alias.team_id).first()
        return None
