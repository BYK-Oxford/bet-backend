from pydantic import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:B11rry2025**@db.zgjotpgtzqiqimolgper.supabase.co:5432/postgres?sslmode=require"

settings = Settings()
