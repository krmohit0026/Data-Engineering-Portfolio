import logging
import httpx
from fastapi import APIRouter, HTTPException
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.models.schemas import StandingRecord, TeamStanding

router = APIRouter(prefix="/standings", tags=["Standings"])
logger = logging.getLogger(__name__)

@router.get("/{competition_code}", response_model=StandingRecord)
async def get_standings(competition_code: str):
    """Fetch live league table for a specific competition"""
    # 1. Use the correct base_url from settings
    url = f"{settings.football_base_url}/competitions/{competition_code}/standings"
    headers = {"X-Auth-Token": settings.football_api_key}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            # Navigate the specific JSON structure of football-data.org
            standing_data = data['standings'][0] 
            
            # 2. Map raw API data to your robust Pydantic Model
            return StandingRecord(
                competition_code=competition_code,
                # Note: Changed 'season' to 'season_year' to match schemas.py
                season_year=data['filters'].get('season', 2024),
                type=standing_data['type'],
                table=[
                    TeamStanding(
                        position=row['position'],
                        team_id=row['team']['id'],         # Required by your schema
                        team_name=row['team']['name'],     # Cleansed via validator in schema
                        played_games=row['playedGames'],
                        won=row['won'],
                        draw=row['draw'],
                        lost=row['lost'],
                        points=row['points'],
                        goals_for=row['goalsFor'],
                        goals_against=row['goalsAgainst'],
                        goal_difference=row['goalDifference'] # Required by your schema
                    ) for row in standing_data['table']
                ]
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"API Error: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail="External API error")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))