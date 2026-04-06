from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Any, List
from datetime import datetime, timezone

# --- 1. MATCH RECORD SCHEMA ---
class MatchRecord(BaseModel):
    """
    Represents a single football match update.
    This schema 'flattens' the nested API response and ensures 
    data types are consistent for Kafka and Snowflake.
    """
    # Use aliases to map API names (id, utcDate) to clean Python names
    match_id: int = Field(alias="id")
    competition_code: str
    season_year: int
    utc_date: str = Field(alias="utcDate")
    status: str
    matchday: Optional[int] = None
    
    # Teams
    home_team: str
    away_team: str
    
    # Scores - Initialized to 0
    home_score: int = 0
    away_score: int = 0
    
    # Metadata: Automatically generated when the object is created
    ingestion_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # --- GUARDRAILS (The Full-Proof Logic) ---
    
    @field_validator("home_score", "away_score", mode="before")
    @classmethod
    def ensure_int_score(cls, v: Any) -> int:
        """
        FAILSAFE: If the API sends None (common for games not yet started),
        we force it to 0 so mathematical enrichments don't crash.
        """
        if v is None:
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        """
        GUARDRAIL: Ensures status is always UPPERCASE (e.g., 'FINISHED').
        This makes SQL filtering in dbt/Snowflake 100% predictable.
        """
        return v.upper() if v else "UNKNOWN"

    model_config = ConfigDict(populate_by_name=True)


# --- 2. TEAM STANDING SUB-SCHEMA ---
class TeamStanding(BaseModel):
    """
    Represents an individual team's row within a league table.
    """
    position: int
    team_id: int 
    team_name: str
    played_games: int = Field(alias="playedGames")
    won: int
    draw: int
    lost: int
    points: int
    goals_for: int = Field(alias="goalsFor")
    goals_against: int = Field(alias="goalsAgainst")
    goal_difference: int = Field(alias="goalDifference")

    @field_validator("team_name")
    @classmethod
    def clean_team_name(cls, v: str) -> str:
        """GUARDRAIL: Basic string cleaning to ensure no trailing spaces."""
        return v.strip() if v else "Unknown Team"

    model_config = ConfigDict(populate_by_name=True)


# --- 3. STANDING RECORD SCHEMA ---
class StandingRecord(BaseModel):
    """
    Represents a full competition standing snapshot (The League Table).
    Used for the slower-moving 'Fundamentals' style ingestion.
    """
    competition_code: str
    season_year: int
    type: str  # TOTAL, HOME, or AWAY
    table: List[TeamStanding]
    
    ingestion_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # --- GUARDRAILS ---
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Ensures table type is one of the allowed API values."""
        allowed = ["TOTAL", "HOME", "AWAY"]
        return v.upper() if v.upper() in allowed else "TOTAL"

    model_config = ConfigDict(populate_by_name=True)