from pydantic import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres.zgjotpgtzqiqimolgper:B11rry2025**@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

settings = Settings()
