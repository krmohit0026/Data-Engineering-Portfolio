# Pydantic Schemas Documentation: schemas.py

## Overview
This file (`schemas.py`) defines the data models (schemas) for the FootballStream API using Pydantic. These schemas serve as the "contract" between your API, Kafka messaging, and Snowflake database, ensuring data consistency, validation, and type safety throughout the entire pipeline.

## Code Breakdown - Line by Line

### 1. Import Statements
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Any, List
from datetime import datetime, timezone
```

**Line 1: Core Pydantic Imports**
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
```

**`BaseModel`**
- **Purpose**: Base class for all data models
- **Usage**: All schemas inherit from this
- **Importance**: Provides automatic validation, serialization, and JSON conversion
- **Why needed**: Foundation for type-safe data handling

**`Field`**
- **Purpose**: Defines field metadata (aliases, defaults, validation)
- **Usage**: Used for field aliases and default values
- **Importance**: Allows mapping API field names to clean Python names
- **Why needed**: Football API uses camelCase, Python uses snake_case

**`field_validator`**
- **Purpose**: Decorator for custom field validation logic
- **Usage**: Applied to methods that validate/transform field values
- **Importance**: "Bulletproof" data validation and transformation
- **Why needed**: Ensures data quality before it enters the pipeline

**`ConfigDict`**
- **Purpose**: Configuration dictionary for model behavior
- **Usage**: Controls model parsing and validation behavior
- **Importance**: Enables advanced Pydantic features
- **Why needed**: Required for `populate_by_name=True`

**Line 2: Type Hints**
```python
from typing import Optional, Any, List
```

**`Optional`**
- **Purpose**: Indicates a field can be None
- **Usage**: Used for optional fields like `matchday`
- **Importance**: Explicit type safety for nullable fields
- **Why needed**: Some API fields may not always be present

**`Any`**
- **Purpose**: Accepts any type (used in validators)
- **Usage**: Parameter type in validation functions
- **Importance**: Flexibility for handling unknown input types
- **Why needed**: API might return unexpected data types

**`List`**
- **Purpose**: Type hint for list collections
- **Usage**: `List[TeamStanding]` for the standings table
- **Importance**: Type safety for collections
- **Why needed**: Standings contain multiple team records

**Line 3: DateTime Imports**
```python
from datetime import datetime, timezone
```

**`datetime`**
- **Purpose**: Date and time handling
- **Usage**: Creating timestamps and parsing dates
- **Importance**: Consistent timestamp generation
- **Why needed**: Ingestion timestamps for data lineage

**`timezone`**
- **Purpose**: Timezone handling (specifically UTC)
- **Usage**: `timezone.utc` for UTC timestamps
- **Importance**: Ensures all timestamps are in UTC
- **Why needed**: Prevents timezone confusion in distributed systems

### 2. MatchRecord Schema
```python
# --- 1. MATCH RECORD SCHEMA ---
class MatchRecord(BaseModel):
    """
    Represents a single football match update.
    This schema 'flattens' the nested API response and ensures 
    data types are consistent for Kafka and Snowflake.
    """
```

**Class Declaration**: `class MatchRecord(BaseModel):`
- **Purpose**: Defines the structure for individual match data
- **Inheritance**: Extends Pydantic's BaseModel
- **Scope**: Single match representation

**Docstring**: Explains the schema's purpose
- **"Flattens"**: Converts nested API JSON to flat structure
- **"Consistent data types"**: Ensures type safety across systems
- **"Kafka and Snowflake"**: End-to-end pipeline compatibility

#### Field Definitions
```python
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
```

**Field Aliases**: `match_id: int = Field(alias="id")`
- **Purpose**: Maps API field name "id" to Python field name "match_id"
- **Why needed**: API uses "id", Python conventions use "match_id"
- **Benefit**: Clean, readable Python code

**Optional Fields**: `matchday: Optional[int] = None`
- **Purpose**: Some matches may not have matchday information
- **Type**: Optional[int] allows None values
- **Why needed**: API doesn't always provide matchday data

**Default Values**: `home_score: int = 0`
- **Purpose**: Initialize scores to 0 for unfinished matches
- **Why needed**: Prevents null values in calculations
- **Benefit**: Mathematical operations always work

**Auto-Generated Timestamps**: `ingestion_timestamp: str = Field(...)`
- **Purpose**: Records when data was ingested into the system
- **Factory**: Lambda function generates timestamp on object creation
- **Format**: ISO format string (e.g., "2026-04-03T10:30:00+00:00")
- **Importance**: Data lineage and audit trail

#### Field Validators
```python
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
```

**Decorator**: `@field_validator("home_score", "away_score", mode="before")`
- **Fields**: Applies to both home_score and away_score
- **Mode**: "before" runs before Pydantic's built-in validation
- **Why needed**: Transform None/null values before type checking

**Logic**:
- **None Check**: `if v is None: return 0`
- **Type Conversion**: `int(v)` attempts conversion
- **Exception Handling**: Catches conversion errors
- **Fallback**: Always returns 0 if conversion fails

**Importance**: Prevents crashes in downstream calculations

```python
@field_validator("status")
@classmethod
def normalize_status(cls, v: str) -> str:
    """
    GUARDRAIL: Ensures status is always UPPERCASE (e.g., 'FINISHED').
    This makes SQL filtering in dbt/Snowflake 100% predictable.
    """
    return v.upper() if v else "UNKNOWN"
```

**Purpose**: Standardizes status values
- **Uppercase**: Ensures consistent casing
- **SQL Friendly**: Predictable filtering in databases
- **Fallback**: "UNKNOWN" if status is empty

**Model Configuration**: `model_config = ConfigDict(populate_by_name=True)`
- **Purpose**: Allows field population by both name and alias
- **Why needed**: Supports both `id` (API) and `match_id` (Python) field access

### 3. TeamStanding Schema
```python
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
```

**Purpose**: Represents one team's standing in a league table
- **Sub-schema**: Used within StandingRecord
- **Fields**: All standard league table statistics
- **Aliases**: Maps camelCase API fields to snake_case Python

**Field Validator**:
```python
@field_validator("team_name")
@classmethod
def clean_team_name(cls, v: str) -> str:
    """GUARDRAIL: Basic string cleaning to ensure no trailing spaces."""
    return v.strip() if v else "Unknown Team"
```

**Purpose**: Cleans team name strings
- **Strip**: Removes leading/trailing whitespace
- **Fallback**: "Unknown Team" if name is empty
- **Why needed**: Prevents display issues and SQL complications

### 4. StandingRecord Schema
```python
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
```

**Purpose**: Complete league standings snapshot
- **Container**: Holds multiple TeamStanding objects
- **Type Field**: TOTAL, HOME, or AWAY standings
- **Table Field**: List of team standings
- **Timestamp**: When standings were captured

## Schema Relationships & Data Flow

```
Football API Response
        ↓
    Pydantic Schemas
        ↓
    Validation & Transformation
        ↓
    Kafka Messages
        ↓
    S3 Storage
        ↓
    Snowflake Tables
        ↓
    dbt Models
```

## Key Design Principles

### 1. **Type Safety**
- **Pydantic Validation**: Ensures data types match expectations
- **Field Validators**: Custom business logic validation
- **Optional Fields**: Explicit handling of nullable data

### 2. **Data Consistency**
- **Field Aliases**: Maps API naming to Python conventions
- **Normalization**: Uppercase status, cleaned strings
- **Defaults**: Sensible defaults prevent null issues

### 3. **Pipeline Compatibility**
- **Flattened Structure**: Nested API data becomes flat records
- **Consistent Types**: Same types across Kafka → S3 → Snowflake
- **Timestamps**: UTC timestamps for global consistency

### 4. **Fail-Safe Design**
- **Null Handling**: Converts None to safe defaults
- **Exception Handling**: Graceful failure in validators
- **Fallback Values**: Always provide usable data

## Usage Examples

### Creating Match Records
```python
# From API response
api_data = {
    "id": 12345,
    "competitionCode": "PL",
    "season": {"year": 2024},
    "utcDate": "2026-04-03T20:00:00Z",
    "status": "finished",
    "homeTeam": {"name": "Manchester United"},
    "awayTeam": {"name": "Liverpool"},
    "score": {"fullTime": {"home": 2, "away": 1}}
}

# Pydantic handles the transformation
match = MatchRecord(**api_data)
print(match.match_id)  # 12345
print(match.status)    # "FINISHED" (normalized)
print(match.home_score)  # 2
```

### Creating Standing Records
```python
standing = StandingRecord(
    competition_code="PL",
    season_year=2024,
    type="TOTAL",
    table=[
        TeamStanding(
            position=1,
            team_id=1,
            team_name="Manchester City",
            played_games=30,
            won=20,
            draw=5,
            lost=5,
            points=65,
            goals_for=60,
            goals_against=25,
            goal_difference=35
        )
    ]
)
```

## Validation Benefits

### Before Schemas (Raw API Data)
```json
{
  "id": null,           // Could be null
  "status": "finished", // Inconsistent casing
  "score": null         // Missing scores
}
```
❌ **Problems**: Null values, inconsistent casing, missing data

### After Schemas (Validated Data)
```json
{
  "match_id": 0,        // Safe default
  "status": "FINISHED", // Consistent uppercase
  "home_score": 0,      // Safe default
  "ingestion_timestamp": "2026-04-03T10:30:00+00:00"
}
```
✅ **Benefits**: Type safety, consistent format, safe defaults

## Integration Points

### FastAPI Integration
```python
from schemas import MatchRecord, StandingRecord

@app.post("/matches")
async def create_match(match_data: MatchRecord):
    # Data is already validated and transformed
    return {"message": "Match recorded", "data": match_data}
```

### Kafka Integration
```python
# Schemas ensure consistent message format
await producer.send("matches", match.dict())
```

### Database Integration
```python
# Snowflake expects consistent column types
INSERT INTO matches SELECT * FROM parsed_json
```

## Testing the Schemas

```python
# Test validation
def test_match_validation():
    # Valid data
    match = MatchRecord(
        id=123,
        competition_code="PL",
        season_year=2024,
        utcDate="2026-04-03T20:00:00Z",
        status="SCHEDULED",
        home_team="Arsenal",
        away_team="Chelsea"
    )
    assert match.status == "SCHEDULED"
    assert match.home_score == 0  # Default
    
    # Test null handling
    match_with_nulls = MatchRecord(
        id=456,
        competition_code="PL", 
        season_year=2024,
        utcDate="2026-04-03T20:00:00Z",
        status="finished",
        home_team="Liverpool",
        away_team="Man City",
        home_score=None,  # Will be converted to 0
        away_score=None   # Will be converted to 0
    )
    assert match_with_nulls.home_score == 0
```

## Schema Evolution

When the Football API changes:

1. **Add new fields** as Optional to maintain backward compatibility
2. **Update validators** if new validation rules are needed
3. **Test thoroughly** with real API data
4. **Update downstream** dbt models if schema changes

## Performance Considerations

- **Validation Overhead**: Pydantic validation has minimal performance impact
- **Memory Usage**: Schemas are lightweight and efficient
- **Serialization**: Fast JSON conversion for Kafka/S3
- **Type Checking**: Compile-time type hints help catch errors early

This schemas.py file is the "data contract" that ensures reliability and consistency across your entire football data pipeline, from API ingestion to Snowflake analytics.</content>
<parameter name="filePath">d:\ironhack\Python Code\Projects\capstone_2\SCHEMAS_DOCUMENTATION.md