from sqlalchemy.orm import Session
from sqlalchemy import func
from app.match_statistics.models.match_statistics_model import MatchStatistics
from app.matches.models.match_model import Match
from app.seasons.models.seasons_model import Season
from app.standings.models.standings_model import Standing
from app.current_league.models.current_league_model import CurrentLeague
from app.teams.models.team_model import Team

class OddsCalculationService:
    def __init__(self, db: Session):
        self.db = db

    async def calculate_ratios_for_matches(self, new_matches):
        """Calculate win, draw, and loss ratios for a list of matches."""
        calculated_ratios_list = []
        for match in new_matches:
            calculated_ratios = await self.calculate_ratios(
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                season_id=match.season_id
            )
            calculated_ratios_list.append(calculated_ratios)
        return calculated_ratios_list

    async def calculate_ratios(self, home_team_id: str, away_team_id: str, season_id: str):
        """Calculate win, draw, and loss ratios for a single match."""
        season = self.db.query(Season).filter(Season.season_id == season_id).first()
        if not season:
            return None

        season_year = season.season_year
        last_season_year = self.get_previous_season_year(season_year)
        last_season = self.db.query(Season).filter(Season.season_year == last_season_year).first()
        last_season_id = last_season.season_id if last_season else None

        home_performance = await self.get_team_season_performance(home_team_id, season_id)
        away_performance = await self.get_team_season_performance(away_team_id, season_id)
        head_to_head = await self.get_head_to_head_record(home_team_id, away_team_id)

        home_team = self.db.query(Team).filter(Team.team_id == home_team_id).first()
        away_team = self.db.query(Team).filter(Team.team_id == away_team_id).first()

        return {
            "home_team": {
                "team_id": home_team.team_id if home_team else None,
                "team_name": home_team.team_name if home_team else "Unknown",
                "current_season": home_performance,
                "last_season": await self.get_team_season_performance(home_team_id, last_season_id) if last_season_id else None
            },
            "away_team": {
                "team_id": away_team.team_id if away_team else None,
                "team_name": away_team.team_name if away_team else "Unknown",
                "current_season": away_performance,
                "last_season": await self.get_team_season_performance(away_team_id, last_season_id) if last_season_id else None
            },
            "head_to_head": head_to_head
        }

    def get_previous_season_year(self, season_year: str) -> str:
        """Get the previous season year given the current season year."""
        if season_year:
            start_year, end_year = map(int, season_year.split("/"))
            return f"{start_year - 1}/{end_year - 1}"
        return None

    
    async def get_team_season_performance(self, team_id: str, season_id: str):
        """Fetch the performance of a team for a given season."""
        if not season_id:
            return None

        current_season = self.db.query(CurrentLeague).filter(
            CurrentLeague.team_id == team_id,
            CurrentLeague.season_id == season_id
        ).first()

        last_season = self.db.query(Standing).filter(
            Standing.team_id == team_id,
            Standing.season_id == season_id
        ).first()

        if not current_season and not last_season:
            return {
                "wins": "0/0", "draws": "0/0", "losses": "0/0",
                "wins_ratio": "0/0", "draws_ratio": "0/0", "losses_ratio": "0/0"
            }

        played = current_season.played if current_season else last_season.played
        wins = current_season.wins if current_season else last_season.wins
        draws = current_season.draws if current_season else last_season.draws
        losses = current_season.losses if current_season else last_season.losses

        return {
            "wins": f"{wins}",
            "draws": f"{draws}",
            "losses": f"{losses}",
            "total_played": f"{played}",
            "wins_ratio": f"{wins}/{played}",
            "draws_ratio": f"{draws}/{played}",
            "losses_ratio": f"{losses}/{played}"
        }

    
    async def get_head_to_head_record(self, home_team_id: str, away_team_id: str):
        """Fetch and calculate the head-to-head record between two teams."""
        total_matches = self.db.query(func.count()).filter(
            ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
            ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id))
        ).scalar()

        if total_matches == 0:
            return {
                "home_wins": "0/0", "away_wins": "0/0", "draws": "0/0",
                "home_win_ratio": "0/0", "away_win_ratio": "0/0", "draw_ratio": "0/0"
            }

        home_wins = self.db.query(func.count()).select_from(Match).join(
            MatchStatistics, Match.match_id == MatchStatistics.match_id
        ).filter(
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id,
            MatchStatistics.full_time_result == "H"
        ).scalar()

        away_wins = self.db.query(func.count()).select_from(Match).join(
            MatchStatistics, Match.match_id == MatchStatistics.match_id
        ).filter(
            Match.home_team_id == away_team_id,
            Match.away_team_id == home_team_id,
            MatchStatistics.full_time_result == "A"
        ).scalar()

        draws = self.db.query(func.count()).select_from(Match).join(
            MatchStatistics, Match.match_id == MatchStatistics.match_id
        ).filter(
            ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
            ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id)),
            MatchStatistics.full_time_result == "D"
        ).scalar()

        return {
            "home_wins": f"{home_wins}",
            "away_wins": f"{away_wins}",
            "draws": f"{draws}",
            "total_matches": f"{total_matches}",
            "home_win_ratio": f"{home_wins}/{total_matches}",
            "away_win_ratio": f"{away_wins}/{total_matches}",
            "draw_ratio": f"{draws}/{total_matches}"
    }
