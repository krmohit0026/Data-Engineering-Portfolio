import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

# --- FIXED ABSOLUTE IMPORTS ---
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.models.schemas import MatchRecord

# Set up logging so we can see what's happening in the console
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/matches",
    tags=["Matches"]
)

@router.get("/{competition_code}", response_model=List[MatchRecord])
async def get_matches(
    competition_code: str,
    # CHANGE: Set default to "FINISHED" so it backfills when no query is sent
    status: Optional[str] = Query("FINISHED", description="Filter by status: SCHEDULED, LIVE, FINISHED")
):
    """
    Fetches matches for a specific competition and flattens them 
    into our bulletproof MatchRecord schema.
    """
    # 1. Prepare the Request
    url = f"{settings.football_base_url}/competitions/{competition_code}/matches"
    headers = {"X-Auth-Token": settings.football_api_key}
    
    # Ensure we use the current season from settings
    params = {"season": settings.football_season}
    
    # This will now use "FINISHED" by default
    if status:
        params["status"] = status.upper()

    # ... [REST OF YOUR CODE REMAINS EXACTLY THE SAME] ...
    # 2. Call the External API safely
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            
            if response.status_code == 429:
                logger.error("API Rate Limit Hit!")
                raise HTTPException(status_code=429, detail="Football API Rate Limit reached.")
            
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"API Error: {e.response.status_code} for {competition_code}")
        raise HTTPException(status_code=e.response.status_code, detail="Error fetching data")
    except Exception as e:
        logger.info(f"Unexpected Connection Error: {e}")
        raise HTTPException(status_code=500, detail="Could not connect to Football API")

    # 3. Extract and Clean the Data
    raw_matches = data.get("matches", [])
    records = []

    for match in raw_matches:
        try:
            score_data = match.get("score", {}).get("fullTime", {})
            records.append(
                MatchRecord(
                    id=match.get("id"),
                    competition_code=competition_code,
                    season_year=settings.football_season,
                    utcDate=match.get("utcDate"),
                    status=match.get("status"),
                    matchday=match.get("matchday"),
                    home_team=match.get("homeTeam", {}).get("name", "Unknown"),
                    away_team=match.get("awayTeam", {}).get("name", "Unknown"),
                    home_score=score_data.get("home"),
                    away_score=score_data.get("away")
                )
            )
        except Exception as schema_err:
            logger.warning(f"Skipping corrupted match record: {schema_err}")
            continue

    return records