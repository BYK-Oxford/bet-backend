from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Create the engine with `pool_pre_ping=True` to prevent stale connections
engine = create_engine(settings.DATABASE_URL,
    pool_pre_ping=True,   # tests connections before using them
    poolclass=NullPool, 
    pool_recycle=1800,    # recycle every 30 min to avoid stale connections
    pool_size=30,          # (optional) max number of persistent connections
    max_overflow=10,      # (optional) extra connections allowed
    pool_timeout=100      # (optional) wait 30s before giving up on a connection
    )

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
    from app.current_league.models.current_league_model import CurrentLeague
    from app.new_odds.models.new_odds_model import NewOdds
    from app.odds_calculation.models.odds_calculation_model import OddsCalculation
    from app.live_data.models.live_game_data import LiveGameData
    
    # Use context manager to ensure connection is released
    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)
