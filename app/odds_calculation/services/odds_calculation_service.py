from sqlalchemy.orm import Session
from sqlalchemy import func
from app.match_statistics.models.match_statistics_model import MatchStatistics
from app.matches.models.match_model import Match
from app.seasons.models.seasons_model import Season
from app.standings.models.standings_model import Standing
from app.current_league.models.current_league_model import CurrentLeague
from app.teams.models.team_model import Team
from app.odds_calculation.services.odds_saving_service import OddsSavingService
from app.leagues.models.leagues_models import League


class OddsCalculationService:
    LAST_SEASON_ID = None
    CURRENT_SEASON_ID=None
    CURRENT_LEAGUE_ID = None

    
    LEAGUE_TIERS = {
        "C1": ["L1", "L2"],   # England
        "C2": ["L3", "L4"],   # Germany
        "C3": ["L5", "L6"],   # Italy
        "C4": ["L7", "L8"],   # Scotland
        "C5": ["L9", "L10"],  # Spain
        "C6": ["L11"],        # Turkey
        "C7": ["L12"]         # France
    }

    def __init__(self, db: Session):
        self.db = db
        self.odds_saving_service = OddsSavingService(db)

    async def calculate_ratios_for_matches(self, new_matches):
        """Calculate win, draw, and loss ratios for a list of matches and save them."""
        results = []

        for match in new_matches:
            print(f"[LOG] Processing match_id: {match.new_odds_id}, Home: {match.home_team_id}, Away: {match.away_team_id}, Date: {match.date}")
            self.__class__.CURRENT_LEAGUE_ID = match.league_id
            odds_data = await self.calculate_ratios(match.home_team_id, match.away_team_id, match.season_id)
            if not odds_data:
                    print(f"[WARN] No odds returned for match_id: {match.new_odds_id}")
                    continue
            try:
                saved_entry = self.odds_saving_service.save_calculated_odds(
                    date=match.date,
                    time=match.time,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    odds_data=odds_data
                )
                print(f"[LOG] Odds saved for match_id: {match.new_odds_id}")
                results.append(saved_entry)
            except Exception as e:
                print(f"[ERROR] Failed to save odds for match_id: {match.new_odds_id}. Error: {e}")
        return results


    async def calculate_ratios(self, home_team_id: str, away_team_id: str, season_id: str):
        """Calculate win, draw, and loss ratios for a single match."""
        season = self.db.query(Season).filter(Season.season_id == season_id).first()
        if not season:
            print(f"[WARN] No season found for season_id: {season_id}")
            return None

        last_season = self.db.query(Season).filter(Season.season_year == self.get_previous_season_year(season.season_year)).first()
        last_season = self.db.query(Season).filter(Season.season_year == self.get_previous_season_year(season.season_year)).first()
        if not last_season:
            print(f"[WARN] No previous season found for year: {self.get_previous_season_year(season.season_year)}")
        last_season_id = last_season.season_id if last_season else None

        self.__class__.LAST_SEASON_ID = last_season_id
        self.__class__.CURRENT_SEASON_ID = season_id

        # Gather data for head-to-head, current season, and last season
        head_to_head = await self.get_head_to_head_record(home_team_id, away_team_id)
        home_team_data = await self.get_team_data(home_team_id, season_id, last_season_id, is_home=True)
        away_team_data = await self.get_team_data(away_team_id, season_id, last_season_id, is_home=False)

        # Calculate weighted draw for home and away teams
        weighted_draw_home = await self.calculate_weighted_draw_ratio(home_team_data["current_season"], home_team_data["last_season"])
        weighted_draw_away = await self.calculate_weighted_draw_ratio(away_team_data["current_season"], away_team_data["last_season"])

        # Final draw chance calculation
        draw_chance = self.calculate_draw_chance(head_to_head['draw_ratio'], weighted_draw_home, weighted_draw_away, head_to_head['total_matches'])

        # Calculate final home win ratio
        final_home_win_ratio = self.calculate_final_home_win_ratio(
            home_team_data.get("weighted_home_win_ratio", 0.0),
            away_team_data.get("weighted_away_loss_ratio", 0.0),
            head_to_head.get("home_win_ratio", 0.0),
            head_to_head['total_matches']
        )

        return {
            "home_team": home_team_data,
            "away_team": away_team_data,
            "head_to_head": head_to_head,
            "final_draw_chance": round(draw_chance, 2),
            "weighted home draw": weighted_draw_home,
            "weighted away draw": weighted_draw_away,
            "final_home_win_ratio": round(final_home_win_ratio, 2),
            "final_away_win_ratio": round(1 - (final_home_win_ratio + draw_chance),2),
        }    

    def get_previous_season_year(self, season_year: str) -> str:
        """Get the previous season year given the current season year."""
        if season_year:
            start_year, end_year = map(int, season_year.split("/"))
            return f"{start_year - 1}/{end_year - 1}"
        return None


    async def get_team_data(self, team_id: str, season_id: str, last_season_id: str, is_home: bool):
        """Retrieve team data including current and previous season performance."""
        team = self.db.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            print(f"[ERROR] No team found for team_id: {team_id}")
            return {}


        # Use class-level variables for current and last season
        current_league_id = self.__class__.CURRENT_LEAGUE_ID

        current_performance = await self.get_team_season_performance(team_id, season_id)
        if not current_performance or current_performance['total_played'] == 0:
            print(f"[WARN] No current season performance for team_id: {team_id}")
        last_performance = await self.get_team_season_performance(team_id, last_season_id) if last_season_id else None
        if not last_performance or last_performance['total_played'] == 0:
            print(f"[WARN] No last season performance for team_id: {team_id}")

        
        # Determine last season league
        last_league_record = self.db.query(Match).filter(
            Match.season_id == last_season_id,
            ((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
        ).first()
        last_league_id = last_league_record.league_id if last_league_record else None
        # Update last_performance with weighted value
        if last_performance and last_league_id:
            current_league = self.db.query(League).filter(League.league_id == current_league_id).first()
            country_id = current_league.country_id if current_league else None
            tiers = self.__class__.LEAGUE_TIERS.get(country_id, [])

            last_tier_index = tiers.index(last_league_id) if last_league_id in tiers else None
            current_tier_index = tiers.index(current_league_id) if current_league_id in tiers else None

            if is_home:
                # Home win adjustment
                if last_league_id == current_league_id:
                    last_performance['wins_ratio'] = (last_performance.get('wins_ratio', 0) or 0) * 1
                elif last_tier_index is not None and current_tier_index is not None:
                    if last_tier_index < current_tier_index:
                        last_performance['wins_ratio'] = (last_performance.get('wins_ratio', 0) or 0) * 2
                    else:
                        last_performance['wins_ratio'] = (last_performance.get('wins_ratio', 0) or 0) * 0.5
                else:
                    last_performance['wins_ratio'] = (last_performance.get('wins_ratio', 0) or 0) * 0.5
            else:
                # Away loss adjustment
                if last_league_id == current_league_id:
                    last_performance['loss_ratio'] = (last_performance.get('loss_ratio', 0) or 0) * 1
                elif last_tier_index is not None and current_tier_index is not None:
                    if last_tier_index < current_tier_index:
                        last_performance['loss_ratio'] = (last_performance.get('loss_ratio', 0) or 0) / 2
                    else:
                        last_performance['loss_ratio'] = (last_performance.get('loss_ratio', 0) or 0) / 0.5
                else:
                    last_performance['loss_ratio'] = (last_performance.get('loss_ratio', 0) or 0) / 2


        team_data = {
            "team_id": team_id,
            "team_name": team.team_name,
            "current_season": current_performance,
            "last_season": last_performance,
        }

        if is_home:
            team_data["weighted_home_win_ratio"] = await self.calculate_weighted_home_win_ratio(current_performance, last_performance)
        else:
            team_data["weighted_away_loss_ratio"] = await self.calculate_weighted_away_loss_ratio(current_performance, last_performance)

        return team_data


    async def get_team_season_performance(self, team_id: str, season_id: str):
        """Fetch the performance of a team for a given season."""
        if not season_id:
            return None

        record = self.db.query(CurrentLeague).filter(CurrentLeague.team_id == team_id, CurrentLeague.season_id == season_id).first()
        if not record:
            record = self.db.query(Standing).filter(Standing.team_id == team_id, Standing.season_id == season_id).first()

        played, wins, draws, losses = (record.played, record.wins, record.draws, record.losses) if record else (0, 0, 0, 0)
    

        return {
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "total_played": played,
            "wins_ratio": wins / played if played else 0.0,
            "draws_ratio": draws / played if played else 0.0,
            "losses_ratio": losses / played if played else 0.0
        }


    async def get_head_to_head_record(self, home_team_id: str, away_team_id: str):
        """Fetch and calculate the head-to-head record between two teams."""
        
        # Count the total matches where home_team_id is home and away_team_id is away
        total_matches = self.db.query(Match.match_id).filter(
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id
        ).order_by(Match.date.desc()).limit(5).all()

        if len(total_matches) == 0:
            return {
                "home_wins": 0, "away_wins": 0, "draws": 0,
                "home_win_ratio": 0.0, "away_win_ratio": 0.0, "draw_ratio": 0.0,
                "total_matches": 0 
            }

        # Count home wins
        home_wins = self.db.query(func.count()).select_from(Match).join(
            MatchStatistics, Match.match_id == MatchStatistics.match_id
        ).filter(
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id,
            MatchStatistics.full_time_result == "H"
        ).scalar()

        # Count away wins
        away_wins = self.db.query(func.count()).select_from(Match).join(
            MatchStatistics, Match.match_id == MatchStatistics.match_id
        ).filter(
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id,
            MatchStatistics.full_time_result == "A"
        ).scalar()

        # Count draws
        draws = self.db.query(func.count()).select_from(Match).join(
            MatchStatistics, Match.match_id == MatchStatistics.match_id
        ).filter(
            (Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id) ,
            MatchStatistics.full_time_result == "D"
        ).scalar()

        return {
            "home_wins": home_wins,
            "away_wins": away_wins,
            "draws": draws,
            "total_matches": len(total_matches),
            "home_win_ratio": home_wins / len(total_matches) if len(total_matches) > 0 else 0.0,
            "away_win_ratio": away_wins / len(total_matches) if len(total_matches) > 0 else 0.0,
            "draw_ratio": draws / len(total_matches) if len(total_matches) > 0 else 0.0
        }


    async def calculate_weighted_home_win_ratio(self, current_performance, last_performance):
        if not current_performance:
            return 0.0

        last_performance = last_performance or {"wins_ratio": 0.0, "total_played": 0}
        total_matches_played = current_performance["total_played"] + last_performance["total_played"]

        if total_matches_played == 0:
            return 0.0

        weighted_home_win_ratio = (
            ((current_performance["wins_ratio"] * current_performance["total_played"])*1.25) +
            ((last_performance["wins_ratio"] * last_performance["total_played"])/1.25)
        ) / total_matches_played

        return weighted_home_win_ratio


    async def calculate_weighted_away_loss_ratio(self, current_performance, last_performance):
        """Calculate the weighted away loss ratio based on home team's wins."""
        if not current_performance:
            return 0.0

        last_performance = last_performance or {"losses_ratio": 0.0, "total_played": 0}
        total_matches_played = current_performance["total_played"] + last_performance["total_played"]

        if total_matches_played == 0:
            return 0.0

        weighted_away_loss_ratio = (
            ((current_performance["losses_ratio"] * current_performance["total_played"])*1.25)+
            ((last_performance["losses_ratio"] * last_performance["total_played"])/1.25)
        ) / total_matches_played

        return weighted_away_loss_ratio


    async def calculate_weighted_draw_ratio(self, current_performance, last_performance):
        """Calculate the weighted draw ratio for a team across two seasons."""
        if not current_performance:
            return 0.0

        last_performance = last_performance or {"draws_ratio": 0.0, "total_played": 0}
        total_matches_played = current_performance["total_played"] + last_performance["total_played"]

        if total_matches_played == 0:
            return 0.0

        weighted_draw_ratio = (
            (current_performance["draws_ratio"] * current_performance["total_played"]) +
            (last_performance["draws_ratio"] * last_performance["total_played"]) 
        ) / total_matches_played

        return weighted_draw_ratio

    def calculate_draw_chance(self, head_to_head_draw_ratio, home_weighted_draw_ratio, away_weighted_draw_ratio, head_to_head_total_matches):
        """Calculate the final draw chance."""
        if head_to_head_total_matches == 0:
            return (home_weighted_draw_ratio + away_weighted_draw_ratio) / 2
        return (head_to_head_draw_ratio + home_weighted_draw_ratio + away_weighted_draw_ratio) / 3


    def calculate_final_home_win_ratio(self, weighted_home_win_ratio, weighted_away_loss_ratio, head_to_head_home_win_ratio, head_to_head_total_matches):
        """Calculate the final home win ratio."""
        if head_to_head_total_matches == 0:
            return (weighted_home_win_ratio + weighted_away_loss_ratio) / 2
        return (weighted_home_win_ratio + weighted_away_loss_ratio + (head_to_head_home_win_ratio*1.25)) / 3

    