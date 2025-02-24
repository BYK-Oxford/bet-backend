from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# Create the engine with `pool_pre_ping=True` to prevent stale connections
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to initialize the database
def init_db():
    # Import all models here
    from app.leagues.models.leagues_models import League
    from app.matches.models.match_model import Match
    from app.teams.models.team_model import Team
    from app.country.models.country_model import Country
    from app.betting_odds.models.betting_odds_model import BettingOdds
    from app.match_statistics.models.match_statistics_model import MatchStatistics
    from app.referee.models.referee_model import Referee
    from app.teams.models.team_alias_model import TeamAlias
    from app.seasons.models.seasons_model import Season
    from app.standings.models.standings_model import Standing
    
    Base.metadata.create_all(bind=engine)
