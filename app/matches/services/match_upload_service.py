import pandas as pd
from io import StringIO
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.core.database import get_db
from app.matches.services.match_service import MatchService
from app.betting_odds.services.betting_odds_service import BettingOddsService
from app.match_statistics.services.match_statistics_service import MatchStatisticsService


class UploadService:

    def __init__(self, db: Session):
        self.db = db
        self.match_service = MatchService(db)
        self.betting_odds_service = BettingOddsService(db)
        self.match_statistics_service = MatchStatisticsService(db)

    def safe_float(self, value):
        try:
            if value in (None, "", "NaN"):
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
        
    def safe_str(self, value):
        if value is None:
            return ""
        if isinstance(value, float) and str(value) == "nan":
            return ""
        return str(value).strip()


    def safe_int(self, value):
        try:
            if value is None:
                return 0
            if isinstance(value, float) and str(value) == "nan":
                return 0
            return int(value)
        except (ValueError, TypeError):
            return 0
        
    async def process_csv(self, file: UploadFile):
        """Reads the CSV, processes data, and calls necessary services."""
        try:
            # Read CSV
            contents = await file.read()
            df = pd.read_csv(StringIO(contents.decode("utf-8")))

             # Normalize: replace empty strings with None
            df = df.replace(r'^\s*$', None, regex=True)

            # Ensure NaN → None
            df = df.where(pd.notnull(df), None)


            for _, row in df.iterrows():
                # Prepare match data
                date = self.safe_str(row.get("Date"))
                time = self.safe_str(row.get("Time"))

                match_data = {
                    "date": f"{date} {time}".strip(),
                    "league": self.safe_str(row.get("Div")),
                    "season": self.safe_str(row.get("Date")),  # you might want a real season field instead
                    "home_team": self.safe_str(row.get("HomeTeam")),
                    "away_team": self.safe_str(row.get("AwayTeam")),
                    "referee": self.safe_str(row.get("Referee")),
                }
                match = self.match_service.create_match(match_data)

                # Prepare betting odds data
                odds_data = {
                    "match_id": match.match_id,
                    "B365H": self.safe_float(row.get("B365H")),
                    "B365D": self.safe_float(row.get("B365D")),
                    "B365A": self.safe_float(row.get("B365A")),
                    "BWH": self.safe_float(row.get("BWH")),
                    "BWD": self.safe_float(row.get("BWD")),
                    "BWA": self.safe_float(row.get("BWA")),
                    "BFH": self.safe_float(row.get("BFH")),
                    "BFD": self.safe_float(row.get("BFD")),
                    "BFA": self.safe_float(row.get("BFA")),
                    "PSH": self.safe_float(row.get("PSH")),
                    "PSD": self.safe_float(row.get("PSD")),
                    "PSA": self.safe_float(row.get("PSA")),
                    "WHH": self.safe_float(row.get("WHH")),
                    "WHD": self.safe_float(row.get("WHD")),
                    "WHA": self.safe_float(row.get("WHA")),
                    "MaxH": self.safe_float(row.get("MaxH")),
                    "MaxD": self.safe_float(row.get("MaxD")),
                    "MaxA": self.safe_float(row.get("MaxA")),
                    "AvgH": self.safe_float(row.get("AvgH")),
                    "AvgD": self.safe_float(row.get("AvgD")),
                    "AvgA": self.safe_float(row.get("AvgA")),
                    "B365_over_2_5": self.safe_float(row.get("B365>2.5")),
                    "B365_under_2_5": self.safe_float(row.get("B365<2.5")),
                    "P_over_2_5": self.safe_float(row.get("P>2.5")),
                    "P_under_2_5": self.safe_float(row.get("P<2.5")),
                    "Max_over_2_5": self.safe_float(row.get("Max>2.5")),
                    "Max_under_2_5": self.safe_float(row.get("Max<2.5")),
                    "Avg_over_2_5": self.safe_float(row.get("Avg>2.5")),
                    "Avg_under_2_5": self.safe_float(row.get("Avg<2.5")),
                    "AHh": self.safe_float(row.get("AHh")),
                    "B365AHH": self.safe_float(row.get("B365AHH")),
                    "B365AHA": self.safe_float(row.get("B365AHA")),
                    "PAHH": self.safe_float(row.get("PAHH")),
                    "PAHA": self.safe_float(row.get("PAHA")),
                    "MaxAHH": self.safe_float(row.get("MaxAHH")),
                    "MaxAHA": self.safe_float(row.get("MaxAHA")),
                    "AvgAHH": self.safe_float(row.get("AvgAHH")),
                    "AvgAHA": self.safe_float(row.get("AvgAHA")),
                }
                self.betting_odds_service.create_betting_odds(odds_data)


                # Prepare match statistics data
                statistics_data = {
                    "full_time_home_goals": self.safe_int(row.get("FTHG")),
                    "full_time_away_goals": self.safe_int(row.get("FTAG")),
                    "full_time_result": self.safe_str(row.get("FTR")),
                    "half_time_home_goals": self.safe_int(row.get("HTHG")),
                    "half_time_away_goals": self.safe_int(row.get("HTAG")),
                    "half_time_result": self.safe_str(row.get("HTR")),
                    "shots_home": self.safe_int(row.get("HS")),
                    "shots_away": self.safe_int(row.get("AS")),
                    "shots_on_target_home": self.safe_int(row.get("HST")),
                    "shots_on_target_away": self.safe_int(row.get("AST")),
                    "fouls_home": self.safe_int(row.get("HF")),
                    "fouls_away": self.safe_int(row.get("AF")),
                    "corners_home": self.safe_int(row.get("HC")),
                    "corners_away": self.safe_int(row.get("AC")),
                    "yellow_cards_home": self.safe_int(row.get("HY")),
                    "yellow_cards_away": self.safe_int(row.get("AY")),
                    "red_cards_home": self.safe_int(row.get("HR")),
                    "red_cards_away": self.safe_int(row.get("AR")),
                }

                match_id = match.match_id
                # Create match statistics
                self.match_statistics_service.create_match_statistics(
                    match_id=match_id, statistics_data=statistics_data
                )

            return {"message": "CSV uploaded and processed successfully"}

        except Exception as e:
            return {"error": f"Failed to process CSV: {str(e)}"}

