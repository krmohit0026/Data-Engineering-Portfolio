import logging
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Internal Imports
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.routers import matches, standings
from Ingestion.football_api.models.schemas import MatchRecord

# 1. Setup Logging - Crucial for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Bulletproof Ingestion API for Football Data",
    version="1.0.0"
)

# 2. Register Routers (Both must be here!)
app.include_router(matches.router)
app.include_router(standings.router)

# 3. PRE-FLIGHT CHECKS (The Failsafes)
@app.on_event("startup")
async def startup_event():
    """
    Runs automatically when the server starts.
    If any check fails, the API will log a CRITICAL error.
    """
    logger.info(f"--- Starting {settings.app_name} Pre-Flight Checks ---")
    
    # Check A: Football API Connectivity & Authentication
    async with httpx.AsyncClient() as client:
        try:
            # Note: Ensure settings.football_base_url is correct in your .env
            test_url = f"{settings.football_base_url}/competitions"
            headers = {"X-Auth-Token": settings.football_api_key}
            response = await client.get(test_url, headers=headers, timeout=5.0)
             
            if response.status_code == 200:
                logger.info("✅ SUCCESS: Football API is reachable and Token is valid.")
            elif response.status_code == 403:
                logger.error("❌ FAILURE: API Token is invalid or restricted.")
            else:
                logger.warning(f"⚠️ WARNING: API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ FAILURE: Could not connect to Football API: {e}")

    # Check B: Environment Variables Check
    logger.info(f"✅ SUCCESS: Loaded {len(settings.competitions)} competitions from .env.")
    logger.info(f"--- Pre-Flight Checks Complete ---")

# 4. HEALTH CHECK & SYSTEM ENDPOINTS
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "configurations": {
            "poll_interval": settings.poll_interval_seconds,
            "monitored_leagues": settings.competitions
        }
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "message": "FootballStream Ingestion API is running.",
        "docs": "/docs",
        "health": "/health"
    }