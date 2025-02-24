from fastapi import FastAPI
import logging
from app.core.database import init_db
from app.api import api_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Ensure database tables are created
@app.on_event("startup")
async def startup():
    try:
        init_db()  # Calls Base.metadata.create_all(bind=engine)
        logger.info("✅ Database connected and tables created.")
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")

@app.get("/")
async def home():
    return {"message": "Welcome to Bet Backend", "database_status": "Connected"}

# Include all API routes
app.include_router(api_router)
