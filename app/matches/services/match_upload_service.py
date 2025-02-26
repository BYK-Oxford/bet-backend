import pandas as pd
from io import StringIO
from sqlalchemy.orm import Session
from fastapi import UploadFile, Depends
from app.core.database import get_db
from app.matches.services.match_service import MatchService
from app.betting_odds.services.betting_odds_service import BettingOddsService
from app.match_statistics.services.match_statistics_service import MatchStatisticsService


class UploadService:

    def __init__(self, db: Session):
        self.db = Depends(get_db)
        self.match_service = MatchService(db)
        self.betting_odds_service = BettingOddsService(db)
        self.match_statistics_service = MatchStatisticsService(db)

    async def process_csv(self, file: UploadFile):
        """Reads the CSV, processes data, and calls necessary services."""
        try:
            # Read CSV
            contents = await file.read()
            df = pd.read_csv(StringIO(contents.decode("utf-8")))

            for _, row in df.iterrows():
                # Prepare match data
                date =  row["Date"]
                time = row["Time"]
                match_data = {
                    "date": f"{date} {time}",
                    "league": row["Div"],
                    "season": row["Date"],
                    "home_team": row["HomeTeam"],
                    "away_team": row["AwayTeam"],
                    "referee": row["Referee"],
                }
                match = self.match_service.create_match(match_data)

                # Prepare betting odds data
                odds_data = {
                   "match_id": match.match_id,

                    # Full-time result odds
                    "B365H": row.get("B365H"),
                    "B365D": row.get("B365D"),
                    "B365A": row.get("B365A"),
                    "BWH": row.get("BWH"),
                    "BWD": row.get("BWD"),
                    "BWA": row.get("BWA"),
                    "BFH": row.get("BFH"),
                    "BFD": row.get("BFD"),
                    "BFA": row.get("BFA"),
                    "PSH": row.get("PSH"),
                    "PSD": row.get("PSD"),
                    "PSA": row.get("PSA"),
                    "WHH": row.get("WHH"),
                    "WHD": row.get("WHD"),
                    "WHA": row.get("WHA"),
                    "MaxH": row.get("MaxH"),
                    "MaxD": row.get("MaxD"),
                    "MaxA": row.get("MaxA"),
                    "AvgH": row.get("AvgH"),
                    "AvgD": row.get("AvgD"),
                    "AvgA": row.get("AvgA"),

                    # Over/Under 2.5 Goals odds
                    "B365_over_2_5": row.get("B365>2.5"),
                    "B365_under_2_5": row.get("B365<2.5"),
                    "P_over_2_5": row.get("P>2.5"),
                    "P_under_2_5": row.get("P<2.5"),
                    "Max_over_2_5": row.get("Max>2.5"),
                    "Max_under_2_5": row.get("Max<2.5"),
                    "Avg_over_2_5": row.get("Avg>2.5"),
                    "Avg_under_2_5": row.get("Avg<2.5"),

                    # Asian Handicap odds
                    "AHh": row.get("AHh"),
                    "B365AHH": row.get("B365AHH"),
                    "B365AHA": row.get("B365AHA"),
                    "PAHH": row.get("PAHH"),
                    "PAHA": row.get("PAHA"),
                    "MaxAHH": row.get("MaxAHH"),
                    "MaxAHA": row.get("MaxAHA"),
                    "AvgAHH": row.get("AvgAHH"),
                    "AvgAHA": row.get("AvgAHA"),
                }

                self.betting_odds_service.create_betting_odds(odds_data)

                # Prepare match statistics data
                statistics_data = {
                    "full_time_home_goals": row.get("FTHG", 0),
                    "full_time_away_goals": row.get("FTAG", 0),
                    "full_time_result": row.get("FTR", ""),
                    "half_time_home_goals": row.get("HTHG", 0),
                    "half_time_away_goals": row.get("HTAG", 0),
                    "half_time_result": row.get("HTR", ""),
                    "shots_home": row.get("HS", 0),
                    "shots_away": row.get("AS", 0),
                    "shots_on_target_home": row.get("HST", 0),
                    "shots_on_target_away": row.get("AST", 0),
                    "fouls_home": row.get("HF", 0),
                    "fouls_away": row.get("AF", 0),
                    "corners_home": row.get("HC", 0),
                    "corners_away": row.get("AC", 0),
                    "yellow_cards_home": row.get("HY", 0),
                    "yellow_cards_away": row.get("AY", 0),
                    "red_cards_home": row.get("HR", 0),
                    "red_cards_away": row.get("AR", 0),
                }

                # Create match statistics
                self.match_statistics_service.create_match_statistics(
                    match_id=match.match_id, statistics_data=statistics_data
                )


            return {"message": "CSV uploaded and processed successfully"}

        except Exception as e:
            return {"error": f"Failed to process CSV: {str(e)}"}
