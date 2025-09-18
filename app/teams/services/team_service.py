import json
from sqlalchemy.orm import Session
from rapidfuzz import fuzz
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
        """Retrieve or create a team, ensuring aliases and fuzzy matching are handled correctly."""
        try:
                
            
            # Step 1: Check if the team name exists as an alias in database
            team_from_alias = self.alias_service.get_team_by_alias(team_name)
            if team_from_alias:
                return team_from_alias

            # Step 2: Check if the team already exists by exact name
            team = self.db.query(Team).filter(Team.team_name == team_name).first()
            if team:
                return team

            # Step 3: Check if this is an alias in our JSON mapping
            for official_name, aliases in self.alias_mapping.items():
                if team_name.lower() in [alias.lower() for alias in aliases] or team_name.lower() == official_name.lower():
                    existing_team = self.db.query(Team).filter(Team.team_name == official_name).first()
                    if not existing_team:
                        for alias in aliases + [official_name]:
                            existing_team = self.alias_service.get_team_by_alias(alias)
                            if existing_team:
                                break
                    
                    if existing_team:
                        self.alias_service.get_or_create_alias(existing_team.team_id, team_name)
                        return existing_team
                    
                    # If no existing team found, create new team
                    league = self.league_service.get_or_create_league(league_name)
                    new_id = generate_custom_id(self.db, Team, "T", "team_id")
                    new_team = Team(
                        team_id=new_id,
                        team_name=official_name,
                        league_id=league.league_id,
                        country_id=league.country_id
                    )
                    self.db.add(new_team)
                    self.db.commit()
                    self.db.refresh(new_team)
                    
                    # Create aliases for all known variations
                    self.alias_service.get_or_create_alias(new_team.team_id, team_name)
                    for alias in aliases:
                        self.alias_service.get_or_create_alias(new_team.team_id, alias)
                    return new_team

            # Step 4: Fuzzy Matching Check
            all_teams = self.db.query(Team).all()
            for existing_team in all_teams:
                # Get all aliases for this team
                aliases = self.alias_service.get_aliases_by_team(existing_team.team_id)
                alias_names = [alias.alias_name.lower() for alias in aliases]
                
                # Compute similarity scores
                similarity_score = fuzz.ratio(team_name.lower(), existing_team.team_name.lower())
                alias_similarity_scores = [fuzz.ratio(team_name.lower(), alias) for alias in alias_names]
                
                # If similarity is high, assume it's the same team
                if similarity_score > 85 or any(score > 85 for score in alias_similarity_scores):
                    self.alias_service.get_or_create_alias(existing_team.team_id, team_name)
                    return existing_team

            # Step 5: If no match found, create new team
            print(f"Warning: Creating new team '{team_name}' not found in alias mapping")
            league = self.league_service.get_or_create_league(league_name)
            new_id = generate_custom_id(self.db, Team, "T", "team_id")
            new_team = Team(
                team_id=new_id,
                team_name=team_name,
                league_id=league.league_id,
                country_id=league.country_id
            )
            self.db.add(new_team)
            self.db.commit()
            self.db.refresh(new_team)

            # Create an alias entry for the team's own name
            self.alias_service.get_or_create_alias(new_team.team_id, team_name)
            return new_team
        except Exception as e:
            self.db.rollback()
            raise e