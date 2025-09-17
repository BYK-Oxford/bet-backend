from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date
from app.odds_calculation.models.odds_calculation_model import OddsCalculation
from app.live_data.services.live_game_date_service import LiveGameDataService
from app.new_odds.models.new_odds_model import NewOdds
from app.leagues.models.leagues_models import League

class OddsRetrievalService:
    def __init__(self, db: Session):
        self.db = db
        self.live_data_service = LiveGameDataService(db)

    def get_all_calculated_odds(self, include_market_data: bool = False):
        """Retrieve all upcoming calculated odds with league & country from NewOdds.
        Optionally include full_market_data for backend use only.
        """
        now = datetime.now().time()
        today = date.today()

        # ✅ Preload teams with joinedload to avoid N+1 queries
        odds = self.db.query(OddsCalculation).options(
            joinedload(OddsCalculation.home_team),
            joinedload(OddsCalculation.away_team),
        ).filter(
            (OddsCalculation.date >= today) |
            ((OddsCalculation.date == today) & (OddsCalculation.time > now))
        ).order_by(
            OddsCalculation.date.asc(), OddsCalculation.time.asc()
        ).all()

        # ✅ Preload leagues and countries
        new_odds = self.db.query(NewOdds).options(
            joinedload(NewOdds.league).joinedload(League.country)
        ).filter(
            (NewOdds.date >= today) |
            ((NewOdds.date == today) & (NewOdds.time > now))
        ).order_by(
            NewOdds.date.asc(), NewOdds.time.asc()
        ).all()

        new_odds_lookup = {
            (o.date, o.time, o.home_team_id, o.away_team_id): o
            for o in new_odds
        }

        # ✅ Bulk-fetch all live data for the odds calculations
        odds_ids = [o.odds_calculation_id for o in odds]
        live_data_lookup = self.live_data_service.get_bulk_live_game_data(odds_ids)

        enriched = []

        for o in odds:
            original = new_odds_lookup.get((o.date, o.time, o.home_team_id, o.away_team_id))
            live_data = live_data_lookup.get(o.odds_calculation_id)

            data = {
                "odds_calculation_id": o.odds_calculation_id,
                "date": o.date,
                "time": o.time,
                "home_team_id": o.home_team_id,
                "home_team_name": o.home_team.team_name if o.home_team else None,
                "home_team_primary_color": o.home_team.home_primary_color if o.home_team else None,
                "home_team_secondary_color": o.home_team.home_secondary_color if o.home_team else None,

                "away_team_id": o.away_team_id,
                "away_team_name": o.away_team.team_name if o.away_team else None,
                "away_team_primary_color": o.away_team.away_primary_color if o.away_team else None,
                "away_team_secondary_color": o.away_team.away_secondary_color if o.away_team else None,

                "match_league": original.league.league_name if original and original.league else None,
                "match_country": original.league.country.country_name if original and original.league and original.league.country else None,

                "calculated_home_chance": o.calculated_home_odds,
                "calculated_draw_chance": o.calculated_draw_odds,
                "calculated_away_chance": o.calculated_away_odds,
                "home_odds": original.home_odds if original else None,
                "draw_odds": original.draw_odds if original else None,
                "away_odds": original.away_odds if original else None,
                "stats_banded_data": o.stats_banded_data if o.stats_banded_data else None,
            }

            if include_market_data:
                data["full_market_data"] = original.full_market_data if original else None

            # ✅ Attach live data if it exists
            if live_data:
                data["live_data"] = {
                    "is_live": live_data.is_live,
                    "scrape_url": live_data.scrape_url,
                    "live_home_score": live_data.live_home_score,
                    "live_away_score": live_data.live_away_score,
                    "match_time": live_data.match_time,
                    "live_home_odds": live_data.live_home_odds,
                    "live_draw_odds": live_data.live_draw_odds,
                    "live_away_odds": live_data.live_away_odds,
                    "shots_on_target_home": live_data.shots_on_target_home,
                    "shots_on_target_away": live_data.shots_on_target_away,
                    "corners_home": live_data.corners_home,
                    "corners_away": live_data.corners_away,
                    "last_updated": live_data.last_updated.isoformat() if live_data.last_updated else None
                }

            enriched.append(data)

        return enriched

    # def get_all_calculated_odds(self, include_market_data: bool = False):
    #     """Retrieve all upcoming calculated odds with league & country from NewOdds.
    #     Optionally include full_market_data for backend use only.
    #     """
        
    #     now = datetime.now().time()
    #     today = date.today()

    #     odds = self.db.query(OddsCalculation).options(
    #         joinedload(OddsCalculation.home_team),
    #         joinedload(OddsCalculation.away_team),
    #     ).filter(
    #         (OddsCalculation.date >= today)|
    #         ((OddsCalculation.date == today) & (OddsCalculation.time > now))
    #     ).order_by(
    #         OddsCalculation.date.asc(), OddsCalculation.time.asc()
    #     ).all()

    #     new_odds = self.db.query(NewOdds).options(
    #         joinedload(NewOdds.league).joinedload(League.country)
    #     ).filter(
    #         (NewOdds.date >= today)|
    #         ((NewOdds.date == today) & (NewOdds.time > now))
    #     ).order_by(
    #         NewOdds.date.asc(), NewOdds.time.asc()
    #     ).all()

    #     new_odds_lookup = {
    #         (o.date, o.time, o.home_team_id, o.away_team_id): o
    #         for o in new_odds
    #     }



    #     enriched = []

    #     for o in odds:
    #         original = new_odds_lookup.get((o.date, o.time, o.home_team_id, o.away_team_id))
    #         live_data = self.live_data_service.get_live_game_data(o.odds_calculation_id)
            
    #         data = {
    #             "odds_calculation_id": o.odds_calculation_id,
    #             "date": o.date,
    #             "time": o.time,
    #             "home_team_id": o.home_team_id,
    #             "home_team_name": o.home_team.team_name if o.home_team else None,
    #             "home_team_primary_color": o.home_team.home_primary_color if o.home_team else None,
    #             "home_team_secondary_color": o.home_team.home_secondary_color if o.home_team else None,

    #             "away_team_id": o.away_team_id,
    #             "away_team_name": o.away_team.team_name if o.away_team else None,
    #             "away_team_primary_color": o.away_team.away_primary_color if o.away_team else None,
    #             "away_team_secondary_color": o.away_team.away_secondary_color if o.away_team else None,

    #             "match_league": original.league.league_name if original and original.league else None,
    #             "match_country": original.league.country.country_name if original and original.league and original.league.country else None,

    #             "calculated_home_chance": o.calculated_home_odds,
    #             "calculated_draw_chance": o.calculated_draw_odds,
    #             "calculated_away_chance": o.calculated_away_odds,
    #             "home_odds": original.home_odds if original else None,
    #             "draw_odds": original.draw_odds if original else None,
    #             "away_odds": original.away_odds if original else None,
    #             "stats_banded_data": o.stats_banded_data if o.stats_banded_data else None,

    #         }

    #         if include_market_data:
    #             data["full_market_data"] = original.full_market_data if original else None
            
    #         # ✅ Attach live data if it exists
    #         if live_data:
    #             data["live_data"] = {
    #                 "is_live": live_data.is_live,
    #                 "scrape_url": live_data.scrape_url,
    #                 "live_home_score": live_data.live_home_score,
    #                 "live_away_score": live_data.live_away_score,
    #                 "match_time": live_data.match_time,
    #                 "live_home_odds": live_data.live_home_odds,
    #                 "live_draw_odds": live_data.live_draw_odds,
    #                 "live_away_odds": live_data.live_away_odds,
    #                 "shots_on_target_home": live_data.shots_on_target_home,
    #                 "shots_on_target_away": live_data.shots_on_target_away,
    #                 "corners_home": live_data.corners_home,
    #                 "corners_away": live_data.corners_away,
    #                 "last_updated": live_data.last_updated.isoformat() if live_data.last_updated else None
    #             }

    #         enriched.append(data)

    #     return enriched


