from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.api import api_router
from app.core.scheduler import start_scheduler 

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


# Allow CORS for all origins (you can restrict it later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; change this for specific domains in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Ensure database tables are created
@app.on_event("startup")
async def startup():
    try:
        init_db()  # Calls Base.metadata.create_all(bind=engine)
        logger.info("✅ Database connected and tables created.")
        start_scheduler()  # ⬅️ Start your cron-based background scheduler here
        logger.info("⏰ Scheduler started.")
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")

@app.get("/")
async def home():
    return {"message": "Welcome to Bet Backend"}

# Include all API routes
app.include_router(api_router)
