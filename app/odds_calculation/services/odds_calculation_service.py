from sqlalchemy.orm import Session
from sqlalchemy import func
from app.match_statistics.models.match_statistics_model import MatchStatistics
from app.matches.models.match_model import Match
from app.seasons.models.seasons_model import Season
from app.standings.models.standings_model import Standing
from app.current_league.models.current_league_model import CurrentLeague
from app.teams.models.team_model import Team
from app.odds_calculation.services.odds_saving_service import OddsSavingService
from app.match_statistics.services.match_statistics_service import MatchStatisticsService
from app.leagues.models.leagues_models import League
from datetime import datetime, timedelta
import re
import os
import pandas as pd
import json
import statistics
import numpy as np
import math

class OddsCalculationService:
    LAST_SEASON_ID = None
    CURRENT_SEASON_ID=None
    CURRENT_LEAGUE_ID = None
    # Class-level attribute for aliases
    TEAM_ALIASES = {}
    HOME_TEAM_STATUS = None
    AWAY_TEAM_STATUS = None

    
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
        self.match_statistics_service = MatchStatisticsService(db)
        # Load aliases once
        if not self.__class__.TEAM_ALIASES:  # only if empty
            try:
                with open("app/teams/teams_aliases.json", "r") as f:
                    self.__class__.TEAM_ALIASES = json.load(f)
            except FileNotFoundError:
                print("[WARN] teams_aliases.json not found. Using empty aliases.")
                self.__class__.TEAM_ALIASES = {}

    async def calculate_ratios_for_matches(self, new_matches):
        """Calculate win, draw, and loss ratios for a list of matches and save them."""
        results = []

        for match in new_matches:
            print(f"[LOG] Processing match_id: {match.new_odds_id}, Home: {match.home_team_id}, Away: {match.away_team_id}, Date: {match.date}")
            self.__class__.CURRENT_LEAGUE_ID = match.league_id
            odds_data = await self.calculate_ratios(match.home_team_id, match.away_team_id, match.season_id)
            banded_data = odds_data.get("stats_banded_data") 
            if not odds_data:
                    print(f"[WARN] No odds returned for match_id: {match.new_odds_id}")
                    continue
            try:
                saved_entry = self.odds_saving_service.save_calculated_odds(
                    date=match.date,
                    time=match.time,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    odds_data=odds_data,
                    stats_metrics=banded_data
                )
                print(f"[LOG] Odds saved for match_id: {match.new_odds_id}")
                results.append(saved_entry)
            except Exception as e:
                print(f"[ERROR] Failed to save odds for match_id: {match.new_odds_id}. Error: {e}")
        return results


    async def calculate_ratios(self, home_team_id: str, away_team_id: str, season_id: str):
        """Calculate win, draw, and loss ratios for a single match."""
        season = self.db.query(Season).filter(Season.season_id == season_id).first()
        
        home_team = self.db.query(Team).filter(Team.team_id == home_team_id).first()
        away_team = self.db.query(Team).filter(Team.team_id == away_team_id).first()
        if not season:
            print(f"[WARN] No season found for season_id: {season_id}")
            return None

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

        
        # ✅ NEW: Detect promoted / relegated / stayed
        home_last_league = self.get_team_league_last_season(home_team_id, last_season_id)
        away_last_league = self.get_team_league_last_season(away_team_id, last_season_id)

        # ✅ Get home team current league code
        home_current_league_row = (
            self.db.query(League.league_code)  # league_code has SP1, I2, etc.
            .join(CurrentLeague, CurrentLeague.league_id == League.league_id)
            .filter(
                CurrentLeague.team_id == home_team_id,
                CurrentLeague.season_id == season_id
            )
            .first()
        )
        home_current_league = home_current_league_row.league_code if home_current_league_row else None

        # ✅ Get away team current league code
        away_current_league_row = (
            self.db.query(League.league_code)
            .join(CurrentLeague, CurrentLeague.league_id == League.league_id)
            .filter(
                CurrentLeague.team_id == away_team_id,
                CurrentLeague.season_id == season_id
            )
            .first()
        )
        away_current_league = away_current_league_row.league_code if away_current_league_row else None

        #print(f"[DEBUG] Home current league code: {home_current_league}, Away current league code: {away_current_league}")



        home_status = self.get_team_status(home_last_league, home_current_league)
        away_status = self.get_team_status(away_last_league, away_current_league)

        #print(f"[DEBUG] {home_team.team_name if home_team else home_team_id} last={home_last_league} current={home_current_league} => {home_status}")
        #print(f"[DEBUG] {away_team.team_name if away_team else away_team_id} last={away_last_league} current={away_current_league} => {away_status}")

        self.__class__.HOME_TEAM_STATUS = home_status
        self.__class__.AWAY_TEAM_STATUS = away_status
        
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
        # print(
        # f"[DEBUG]Result | {home_team.team_name if home_team else home_team_id} "
        # f"vs {away_team.team_name if away_team else away_team_id} => "
        # f"HomeWin={final_home_win_ratio:.2f}, Draw={draw_chance:.2f}, "
        # f"AwayWin={1 - (final_home_win_ratio + draw_chance):.2f}"
        # )

        adjusted_home, adjusted_away, adjusted_draw = self.adjust_ratios_by_status(final_home_win_ratio,(1 - (final_home_win_ratio + draw_chance)),draw_chance,home_status,away_status)
        #print(f"Adj after league stats : ADJ_HOME {adjusted_home}, ADJ_AWAY {adjusted_away}, ADJ_DRW {adjusted_draw}")
        final_adj_home, final_adj_away, final_adj_draw = self.final_95_check(adjusted_home, adjusted_away, adjusted_draw)
        #print(f"Adj after 0.95 : ADJ_HOME {final_adj_home}, ADJ_AWAY {final_adj_away}, ADJ_DRW {final_adj_draw}")

        # Fetch historic stats for this matchup
        historic_matches_raw = self.match_statistics_service.get_historic_stats_for_banded_chart(
            home_team_id, away_team_id
        )

        # Reformat to match calculate_historic_metrics expectations
        historic_matches = []
        for match in historic_matches_raw:
            historic_matches.append({
                "date": match["date"],
                "statistics": {
                    "shots_home": match.get("shots_home", 0),
                    "shots_away": match.get("shots_away", 0),
                    "shots_on_target_home": match["shots_on_target_home"],
                    "shots_on_target_away": match["shots_on_target_away"],
                    "corners_home": match["corners_home"],
                    "corners_away": match["corners_away"],
                    "full_time_home_goals": match.get("full_time_home_goals", 0),
                    "full_time_away_goals": match.get("full_time_away_goals", 0)
                }
            })

        # Now calculate banded metrics
        banded_data = self.calculate_historic_metrics(historic_matches)

        return {
            "home_team": home_team_data,
            "away_team": away_team_data,
            "head_to_head": head_to_head,
            "final_draw_chance": round(final_adj_draw,3),
            "weighted home draw": weighted_draw_home,
            "weighted away draw": weighted_draw_away,
            "final_home_win_ratio": round(final_adj_home,3),
            "final_away_win_ratio": round(final_adj_away,3),
            "stats_banded_data": banded_data
        }  
    
    def final_95_check(
        self,
        adj_home_win: float,
        adj_away_win: float,
        adj_draw: float,
    )-> tuple[float, float, float]:
        '''
            check if any part is above 0.95 and start adjusting both
        
        '''
        if adj_home_win >= 0.95:
            adjustment2 = 0.10
            to_draw2 = adjustment2 * 0.30
            to_other2 = adjustment2 - to_draw2
            final_adj_home = adj_home_win - adjustment2
            final_adj_draw = adj_draw + to_draw2
            final_adj_away = adj_away_win + to_other2
        elif adj_away_win >=0.95:
            adjustment2 = 0.10
            to_draw2 = adjustment2 * 0.30
            to_other2 = adjustment2 - to_draw2
            final_adj_away = adj_away_win - adjustment2
            final_adj_draw = adj_draw + to_draw2
            final_adj_home = adj_home_win + to_other2
        else:
            final_adj_away = adj_away_win
            final_adj_draw = adj_draw
            final_adj_home = adj_home_win


        return (final_adj_home, final_adj_away, final_adj_draw)

    def adjust_ratios_by_status(
        self,
        home_win: float,
        away_win: float,
        draw: float,
        home_status: str,
        away_status: str
    ) -> tuple[float, float, float]:
        """
        Adjusts win/draw ratios based on team status (promoted, relegated, stayed).
        
        Rules:
        - stayed vs stayed → no adjustment
        - promoted vs stayed → promoted loses 0.20
            - 20% of 0.20 → draw
            - 80% of 0.20 → stayed team
        - relegated vs promoted → promoted loses 0.30
            - 20% of 0.30 → draw
            - 80% of 0.30 → relegated team
        """

        adjustment = 0.0
        to_draw = 0.0
        to_other = 0.0
        home_win_adjusted, away_win_adjusted, draw_adjusted = home_win, away_win , draw

        # Case 1: stayed vs stayed & promoted vs promoted & relegated vs relegated
        if home_status == "stayed" and away_status == "stayed":
            return (home_win_adjusted, away_win_adjusted, draw_adjusted)
        elif home_status == "promoted" and away_status == "promoted":
            return (home_win_adjusted, away_win_adjusted, draw_adjusted)
        elif home_status == "relegated" and away_status == "relegated":
            return (home_win_adjusted, away_win_adjusted, draw_adjusted)

        # Case 2: promoted vs stayed
        if home_status == "promoted" and away_status == "stayed" and home_win > 0.20:
            adjustment = 0.20
            to_draw = adjustment * 0.20 
            to_other = adjustment-to_draw
            home_win_adjusted = home_win - adjustment
            away_win_adjusted = away_win + to_other
            draw_adjusted = draw + to_draw

        elif home_status == "stayed" and away_status == "promoted" and away_win > 0.20:
            adjustment = 0.20
            to_draw = adjustment * 0.20
            to_other = adjustment-to_draw
            away_win_adjusted = away_win - adjustment
            home_win_adjusted = home_win + to_other
            draw_adjusted = draw + to_draw

        #case 3 relegated vs stayed con
        if home_status == "relegated" and away_status == "stayed" and away_win > 0.20:
            adjustment = 0.20
            to_draw = adjustment * 0.20 
            to_other = adjustment-to_draw
            home_win_adjusted = home_win + to_other
            away_win_adjusted = away_win - adjustment
            draw_adjusted = draw + to_draw

        elif home_status == "stayed" and away_status == "relegated" and home_win > 0.20:
            adjustment = 0.20
            to_draw = adjustment * 0.20
            to_other = adjustment-to_draw
            away_win_adjusted = away_win + to_other
            home_win_adjusted = home_win - adjustment
            draw_adjusted = draw + to_draw

        # Case 3: promoted vs relegated
        elif home_status == "promoted" and away_status == "relegated" and home_win > 0.30:
            adjustment = 0.30
            to_draw = adjustment * 0.20
            to_other = adjustment-to_draw
            home_win_adjusted = home_win - adjustment
            away_win_adjusted = away_win + to_other
            draw_adjusted = draw + to_draw

        elif home_status == "relegated" and away_status == "promoted" and away_win > 0.30:
            adjustment = 0.30
            to_draw = adjustment * 0.20
            to_other = adjustment-to_draw
            away_win_adjusted = away_win - adjustment
            home_win_adjusted = home_win +  to_other
            draw_adjusted = draw + to_draw

        else:
            return (home_win_adjusted, away_win_adjusted, draw_adjusted)

        return (home_win_adjusted, away_win_adjusted, draw_adjusted)
  

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
        team_name = team.team_name if team else team_id
        season = self.db.query(Season).filter(Season.season_id == season_id).first()
        season_name = season.season_year if season else season_id

        last_season_name = None
        if last_season_id:
            last_season = self.db.query(Season).filter(Season.season_id == last_season_id).first()
            last_season_name = last_season.season_year if last_season else last_season_id


        current_performance = await self.get_team_season_performance(team_id, season_id)
        if not current_performance or current_performance['total_played'] == 0:
            print(f"[WARN] No current season performance for team_id: {team_id}")
        last_performance = await self.get_team_season_performance(team_id, last_season_id) if last_season_id else None
        if not last_performance or last_performance['total_played'] == 0:
            print(f"[WARN] No last season performance for team_id: {team_id}")

        #print(f"[DEBUG] {team_name} | Current Season {season_name} Performance => {current_performance}")
        if last_performance:
            print(f"[DEBUG] {team_name} | Last Season {last_season_name} Performance => {last_performance}")

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
        
        team = self.db.query(Team).filter(Team.team_id == team_id).first()
        season = self.db.query(Season).filter(Season.season_id == season_id).first()
        team_name = team.team_name if team else team_id
        season_name = season.season_year if season else season_id

        #print(f"[DEBUG] get_team_season_performance START | {team_name} ({team_id}), Season: {season_name}")

    

        record = self.db.query(CurrentLeague).filter(CurrentLeague.team_id == team_id, CurrentLeague.season_id == season_id).first()
        if not record:
            record = self.db.query(Standing).filter(Standing.team_id == team_id, Standing.season_id == season_id).first()

        if record:
            played, wins, draws, losses = record.played, record.wins, record.draws, record.losses
        else:
             # Fallback to CSV
            csv_path = os.path.join(os.path.dirname(__file__), "last_season.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                team_row = None

                # Normalize CSV names
                df["Team_clean"] = df["Team"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
                team_name_clean = team_name.lower().replace(" ", "").replace("&", "")

                team_row = None
                for real_name, aliases in self.__class__.TEAM_ALIASES.items():
                    for alias in aliases:
                        alias_clean = alias.lower().replace(" ", "").replace("&", "")
                        if team_name_clean == alias_clean:
                            # Try to find a matching row in CSV
                            for csv_alias in aliases:
                                csv_alias_clean = csv_alias.lower().replace(" ", "").replace("&", "")
                                matched_row = df[df["Team_clean"] == csv_alias_clean]
                                if not matched_row.empty:
                                    team_row = matched_row.iloc[0]
                                    break
                            if team_row is not None:
                                break
                    if team_row is not None:
                        break
                
                if team_row is not None:
                    played = float(team_row.get("Played", 0))
                    wins = float(team_row.get("Wins", 0))
                    draws = float(team_row.get("Draws", 0))
                    losses = float(team_row.get("Losses", 0))
                else:
                    print(f"[WARN] Team {team_name} not found in last_season.csv using aliases")
                    played, wins, draws, losses = 0, 0, 0, 0
            else:
                print(f"[WARN] last_season.csv not found")
                played, wins, draws, losses = 0, 0, 0, 0


        result = {
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "total_played": played,
        "wins_ratio": float(wins / played) if played else 0,
        "draws_ratio": float(draws / played) if played else 0,
        "losses_ratio": float(losses / played) if played else 0
        }

        #print(f"[DEBUG] Season Perf | {team_name} ({season_name}) => {result}")
        return result


    async def get_head_to_head_record(self, home_team_id: str, away_team_id: str):
        """Fetch and calculate the head-to-head record between two teams."""
        home_team = self.db.query(Team).filter(Team.team_id == home_team_id).first()
        away_team = self.db.query(Team).filter(Team.team_id == away_team_id).first()
        #print(f"[DEBUG] H2H START | {home_team.team_name if home_team else home_team_id} vs {away_team.team_name if away_team else away_team_id}")

    
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
        
        # print(f"[DEBUG] H2H Last 5 => home_wins={home_wins}, draws={draws}, away_wins={away_wins}, "
        #   f"ratios=H:{home_wins / len(total_matches) if len(total_matches) > 0 else 0.0:.2f} D:{draws / len(total_matches) if len(total_matches) > 0 else 0.0:.2f} A:{away_wins / len(total_matches) if len(total_matches) > 0 else 0.0:.2f}")
        
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
            (((current_performance["wins_ratio"] * current_performance["total_played"])*1.25 if (current_performance["wins_ratio"] * current_performance["total_played"]) < 0.8 else (current_performance["wins_ratio"] * current_performance["total_played"]))) +
            ((last_performance["wins_ratio"] * last_performance["total_played"])/1.25)
        ) / total_matches_played

        #print(f"[DEBUG] Weighted Home Win => {weighted_home_win_ratio:.4f}")

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
            (((current_performance["losses_ratio"] * current_performance["total_played"])*1.25)if (current_performance["losses_ratio"] * current_performance["total_played"]) < 0.8 else (current_performance["losses_ratio"] * current_performance["total_played"])  )+
            ((last_performance["losses_ratio"] * last_performance["total_played"])/1.25)
        ) / total_matches_played
       
        #print(f"[DEBUG] Weighted Away Loss => {weighted_away_loss_ratio:.4f}")

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

        #print(f"[DEBUG] Weighted Draw => {weighted_draw_ratio:.4f}")

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
        return (weighted_home_win_ratio + weighted_away_loss_ratio + ((head_to_head_home_win_ratio * 1.25 if head_to_head_home_win_ratio < 0.8 else head_to_head_home_win_ratio))) / 3

    def parse_league_tier(self, league_code: str):
        """
        Parse league code into (country_code, tier_number).
        Example: E0 -> (E, 0), E1 -> (E, 1), SP2 -> (SP, 2), D1 -> (D, 1).
        """
        match = re.match(r"([A-Z]+)(\d+)", league_code)
        if not match:
            return None, None
        country = match.group(1)
        tier = int(match.group(2))
        return country, tier

    def get_team_league_last_season(self, team_id: str, last_season_id: str):
        """Find the league a team played in last season. If not found, assume promoted from 3rd tier."""
        # Get any match played by this team last season
        match_record = (
            self.db.query(Match)
            .filter(
                Match.season_id == last_season_id,
                ((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
            )
            .first()
        )

        if match_record:
            # Join League table to get the league code
            league = self.db.query(League).filter(League.league_id == match_record.league_id).first()
            if league:
                return league.league_code

        # If no match found, assume team was promoted from 3rd tier
        return "PROMOTED_FROM_L3"

    def get_team_status(self, last_league_code: str, current_league_code: str):
        """Determine if team stayed, promoted, or relegated based on league codes."""
        if not last_league_code or not current_league_code:
            return "unknown"

        if last_league_code == "PROMOTED_FROM_L3":
            return "promoted"

        last_country, last_tier = self.parse_league_tier(last_league_code)
        curr_country, curr_tier = self.parse_league_tier(current_league_code)

        if not last_country or not curr_country or last_country != curr_country:
            return "unknown"

        # Stayed
        if last_tier == curr_tier:
            return "stayed"
        # Relegated → tier number increased (0 → 1)
        elif last_tier < curr_tier:
            return "relegated"
        # Promoted → tier number decreased (1 → 0)
        elif last_tier > curr_tier:
            return "promoted"

        return "unknown"
    
    def compute_banded_stats(self, avg: float) -> list:
        """Distribute avg across 90 minutes and add ±25% range (same as frontend)."""
        time_intervals = [0, 15, 30, 45, 60, 75, 90]
        per_min = avg / 90 if avg else 0
        banded = []
        for t in time_intervals:
            val = round(per_min * t, 2)
            if t == 0:
                banded.append({"time": t, "actual": val, "stdRange": [0, 0]})
            else:
                std = val * 0.25
                banded.append({
                    "time": t,
                    "actual": val,
                    "stdRange": [round(max(val - std, 0), 2), round(val + std, 2)]
                })
        return banded


    def compute_correlation(self, matches, stat_key: str):
        home_stats, home_goals = [], []
        away_stats, away_goals = [], []

        for m in matches:
            stats = m["statistics"]

            if stat_key == "corners":
                home_val = stats.get("corners_home", 0)
                away_val = stats.get("corners_away", 0)

            elif stat_key == "shots_on_target":
                home_val = stats.get("shots_on_target_home", 0)
                away_val = stats.get("shots_on_target_away", 0)

            else:
                continue

            # Only append if values exist
            if home_val is not None:
                home_stats.append(home_val)
                home_goals.append(stats.get("full_time_home_goals", 0))
            if away_val is not None:
                away_stats.append(away_val)
                away_goals.append(stats.get("full_time_away_goals", 0))

        def safe_corr(x, y):
            if len(x) < 2 or len(y) < 2 or np.std(x) == 0 or np.std(y) == 0:
                return 0
            corr = float(np.corrcoef(x, y)[0, 1])
            return 0 if math.isnan(corr) or math.isinf(corr) else corr

        return {
            "home_correlation": safe_corr(home_stats, home_goals),
            "away_correlation": safe_corr(away_stats, away_goals),
        }


    def calculate_historic_metrics(self, historic_matches):
        import math
        import statistics
        import numpy as np

        # ✅ Only keep corners & shots_on_target
        stats_keys = ["corners", "shots_on_target"]

        if not historic_matches:
            return {
                key: {
                    "home": self.compute_banded_stats(0),
                    "away": self.compute_banded_stats(0),
                    "home_correlation": 0,
                    "away_correlation": 0
                } for key in stats_keys
            }

        today = datetime.now()
        # Cutoffs
        cutoff_sd = today - timedelta(days=5*365)
        cutoff_corr = today - timedelta(days=3*365)

        def get_match_date(m):
            """Extract just the date from a datetime or string."""
            match_date = m.get("date")
            if isinstance(match_date, datetime):
                return match_date.date()
            elif match_date:
                return datetime.strptime(str(match_date).split(" ")[0], "%Y-%m-%d").date()
            return None

        # Filter for SD (last 5 years)
        matches_for_sd = [
            m for m in historic_matches
            if (d := get_match_date(m)) and d >= cutoff_sd.date()
        ]

        # Filter for correlation (last 3 years, but cap at 3 latest matches)
        matches_for_corr = [
            m for m in historic_matches
            if (d := get_match_date(m)) and d >= cutoff_corr.date()
        ]
        matches_for_corr = sorted(matches_for_corr, key=lambda m: get_match_date(m), reverse=True)[:3]

        banded_data = {}

        for key in stats_keys:
            home_vals, away_vals = [], []

            for m in matches_for_sd:
                stats = m.get("statistics", {})
                home_val = stats.get(f"{key}_home", 0)
                away_val = stats.get(f"{key}_away", 0)

                home_vals.append(home_val if home_val is not None else 0)
                away_vals.append(away_val if away_val is not None else 0)

            avg_home = statistics.mean(home_vals) if home_vals else 0
            avg_away = statistics.mean(away_vals) if away_vals else 0

            correlations = self.compute_correlation(matches_for_corr, key)
            home_corr = correlations.get("home_correlation", 0)
            away_corr = correlations.get("away_correlation", 0)
            home_corr = 0 if math.isnan(home_corr) or math.isinf(home_corr) else home_corr
            away_corr = 0 if math.isnan(away_corr) or math.isinf(away_corr) else away_corr

            banded_data[key] = {
                "home": self.compute_banded_stats(avg_home),
                "away": self.compute_banded_stats(avg_away),
                "home_correlation": home_corr,
                "away_correlation": away_corr,
            }

        return banded_data
