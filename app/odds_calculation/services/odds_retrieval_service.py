from sqlalchemy.orm import Session, joinedload
from app.odds_calculation.models.odds_calculation_model import OddsCalculation
from app.new_odds.models.new_odds_model import NewOdds
from app.teams.models.team_model import Team
from app.leagues.models.leagues_models import League

class OddsRetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_calculated_odds(self):
        """Retrieve all calculated odds along with original bookmaker odds, team names, and league names."""
        # Get all calculated odds with team/league info
        odds = self.db.query(OddsCalculation).options(
            joinedload(OddsCalculation.home_team).joinedload(Team.league),
            joinedload(OddsCalculation.away_team).joinedload(Team.league),
        ).all()

        # Fetch all original odds from NewOdds (we’ll match in memory)
        new_odds = self.db.query(NewOdds).all()

        # Create a lookup dictionary for fast matching
        new_odds_lookup = {
            (o.date, o.time, o.home_team_id, o.away_team_id): o
            for o in new_odds
        }

        enriched = []
        for o in odds:
            original = new_odds_lookup.get((o.date, o.time, o.home_team_id, o.away_team_id))
            enriched.append({
                "odds_calculation_id": o.odds_calculation_id,
                "date": o.date,
                "time": o.time,
                "home_team_id": o.home_team_id,
                "home_team_name": o.home_team.team_name if o.home_team else None,
                "home_team_league": o.home_team.league.league_name if o.home_team and o.home_team.league else None,
                "away_team_id": o.away_team_id,
                "away_team_name": o.away_team.team_name if o.away_team else None,
                "away_team_league": o.away_team.league.league_name if o.away_team and o.away_team.league else None,
                "calculated_home_chance": o.calculated_home_odds,
                "calculated_draw_chance": o.calculated_draw_odds,
                "calculated_away_chance": o.calculated_away_odds,
                "home_odds": original.home_odds if original else None,
                "draw_odds": original.draw_odds if original else None,
                "away_odds": original.away_odds if original else None,
            })

        return enriched
