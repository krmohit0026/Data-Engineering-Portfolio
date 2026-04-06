# FastAPI Standings Router Documentation: standings.py

## Overview
This file (`standings.py`) implements the standings endpoint for the FootballStream API. It fetches league table data from the external Football-Data.org API, processes the nested JSON structure, and returns it in a structured format for downstream analytics and BI tools.

## Code Breakdown - Line by Line

### 1. Import Statements
```python
import logging
import httpx
from fastapi import APIRouter, HTTPException
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.models.schemas import StandingRecord, TeamStanding
```

**Line 1: `import logging`**
- **Purpose**: Imports Python's logging module
- **Usage**: Used for error tracking and API call monitoring
- **Importance**: Critical for debugging external API issues
- **Why needed**: League standings are slower-moving but still require monitoring

**Line 2: `import httpx`**
- **Purpose**: Imports the async HTTP client library
- **Usage**: Makes non-blocking HTTP requests to Football API
- **Importance**: Enables async FastAPI endpoints
- **Why needed**: FastAPI requires async HTTP clients for performance

**Line 3: FastAPI Components**
```python
from fastapi import APIRouter, HTTPException
```

**`APIRouter`**
- **Purpose**: Creates a modular router for standings endpoints
- **Usage**: Groups standings routes under `/standings` prefix
- **Importance**: Modular API design, separates concerns
- **Why needed**: Keeps standings logic isolated from matches/other endpoints

**`HTTPException`**
- **Purpose**: Raises proper HTTP error responses
- **Usage**: Returns appropriate status codes for API failures
- **Importance**: Clear error communication to API consumers
- **Why needed**: External API failures need proper error handling

**Lines 4-5: Internal Imports**
```python
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.models.schemas import StandingRecord, TeamStanding
```

**`settings`**
- **Purpose**: Imports the global configuration singleton
- **Usage**: Accesses API URLs, authentication keys, and seasons
- **Importance**: Centralized configuration management
- **Why needed**: All API parameters must come from validated config

**`StandingRecord, TeamStanding`**
- **Purpose**: Imports Pydantic schemas for data validation
- **Usage**: Structures and validates league table data
- **Importance**: Ensures data consistency across the pipeline
- **Why needed**: "Bulletproof" validation for league standings data

### 2. Router and Logger Setup
```python
router = APIRouter(prefix="/standings", tags=["Standings"])
logger = logging.getLogger(__name__)
```

**Router Creation**: `router = APIRouter(prefix="/standings", tags=["Standings"])`
- **Prefix**: All routes accessible under `/standings`
- **Tags**: Groups endpoints in API docs under "Standings"
- **Modularity**: Can be imported and registered in main.py
- **Organization**: Keeps standings logic separate from matches

**Logger Setup**: `logger = logging.getLogger(__name__)`
- **Module-specific**: Uses `__name__` for proper log categorization
- **Hierarchy**: Inherits root logger configuration
- **Usage**: All logging in this module uses this logger
- **Importance**: Enables filtering logs by component

### 3. Endpoint Definition
```python
@router.get("/{competition_code}", response_model=StandingRecord)
async def get_standings(competition_code: str):
```

**Decorator**: `@router.get("/{competition_code}", response_model=StandingRecord)`
- **HTTP Method**: GET request
- **Path Parameter**: `{competition_code}` (e.g., "PL", "CL", "BL1")
- **Response Model**: Returns a single StandingRecord object
- **Type Safety**: FastAPI validates response against Pydantic schema

**Function Signature**: `async def get_standings(competition_code: str):`
- **Parameter**: Competition code from URL path
- **Async**: Required for non-blocking HTTP calls
- **Return**: Validated StandingRecord with league table data

### 4. Function Docstring
```python
"""Fetch live league table for a specific competition"""
```

**Purpose**: Documents the endpoint's functionality
- **"Fetch live"**: Indicates current standings data
- **"League table"**: Describes the data structure returned
- **"Specific competition"**: Clarifies the path parameter requirement
- **Importance**: Clear API documentation for consumers

### 5. API Request Preparation
```python
# 1. Use the correct base_url from settings
url = f"{settings.football_base_url}/competitions/{competition_code}/standings"
headers = {"X-Auth-Token": settings.football_api_key}
```

**Comment**: `# 1. Use the correct base_url from settings`
- **Purpose**: Documents the importance of using configured URLs
- **Why important**: Ensures consistency across environments

**URL Construction**: `url = f"{settings.football_base_url}/competitions/{competition_code}/standings"`
- **Dynamic**: Uses configured base URL and path parameter
- **Endpoint**: Football API standings endpoint
- **Example**: `https://api.football-data.org/v4/competitions/PL/standings`

**Headers**: `headers = {"X-Auth-Token": settings.football_api_key}`
- **Authentication**: Required by Football-Data.org API
- **Format**: "X-Auth-Token" header as per API specification
- **Security**: Uses validated API key from configuration

### 6. API Call with Error Handling
```python
async with httpx.AsyncClient() as client:
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()
```

**Context Manager**: `async with httpx.AsyncClient() as client:`
- **Resource Management**: Automatic connection cleanup
- **Async**: Non-blocking HTTP operations
- **Best Practice**: Proper resource lifecycle management

**HTTP Request**: `response = await client.get(url, headers=headers, timeout=10.0)`
- **Method**: GET request to standings endpoint
- **Timeout**: 10 seconds prevents hanging requests
- **Authentication**: Includes auth headers

**Error Checking**: `response.raise_for_status()`
- **Automatic**: Raises exception for HTTP error status codes
- **Convenience**: Single line handles 4xx/5xx errors
- **Consistency**: Standard HTTP error handling pattern

**Data Parsing**: `data = response.json()`
- **JSON Conversion**: Parses API response to Python dict
- **Assumption**: API returns valid JSON
- **Efficiency**: Parse once, use throughout function

### 7. Data Structure Navigation
```python
# Navigate the specific JSON structure of football-data.org
standing_data = data['standings'][0]
```

**Comment**: `# Navigate the specific JSON structure of football-data.org`
- **Purpose**: Documents the need to understand API response format
- **Why important**: External APIs have specific data structures

**Data Extraction**: `standing_data = data['standings'][0]`
- **API Structure**: Football API returns array of standings objects
- **Index [0]**: Takes the first (usually only) standings table
- **Navigation**: Accesses the league table data structure

### 8. Schema Mapping and Validation
```python
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
```

**Comment**: `# 2. Map raw API data to your robust Pydantic Model`
- **Purpose**: Documents the transformation from API to schema
- **Why important**: Raw API data needs validation and structure

**StandingRecord Creation**: Main container object
- **competition_code**: From URL parameter
- **season_year**: From API filters, defaults to 2024
- **type**: Standing type (TOTAL, HOME, AWAY) from API
- **table**: List of TeamStanding objects

**Season Handling**: `season_year=data['filters'].get('season', 2024)`
- **Safe Access**: Uses `.get()` for missing data
- **Default**: Falls back to 2024 if not provided
- **Type Consistency**: Matches schema expectations

**Table Creation**: List comprehension for team standings
- **Iteration**: Processes each team in the league table
- **Transformation**: Maps API fields to schema fields
- **Validation**: Each TeamStanding goes through Pydantic validation

**Field Mapping Details**:
- **position**: Team's league position
- **team_id**: Unique team identifier (required)
- **team_name**: Team name (validated for cleanliness)
- **played_games**: Matches played (API: playedGames)
- **won/draw/lost**: Match results
- **points**: League points
- **goals_for/against**: Goal statistics (API: goalsFor/goalsAgainst)
- **goal_difference**: Goal difference (API: goalDifference)

### 9. Exception Handling
```python
except httpx.HTTPStatusError as e:
    logger.error(f"API Error: {e.response.text}")
    raise HTTPException(status_code=e.response.status_code, detail="External API error")
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

**HTTPStatusError**: Specific handling for HTTP errors
- **Logging**: Records full error response text
- **Propagation**: Raises FastAPI exception with same status code
- **User Feedback**: Generic "External API error" message

**Generic Exception**: Catches all other errors
- **Logging**: Records error details for debugging
- **Fallback**: Returns 500 Internal Server Error
- **Safety**: Never exposes internal error details to users

## API Usage Examples

### Get Premier League Standings
```bash
GET /standings/PL
# Returns current Premier League table
```

### Get Champions League Standings
```bash
GET /standings/CL
# Returns Champions League group standings
```

### Get Bundesliga Standings
```bash
GET /standings/BL1
# Returns Bundesliga league table
```

## Response Structure

```json
{
  "competition_code": "PL",
  "season_year": 2024,
  "type": "TOTAL",
  "table": [
    {
      "position": 1,
      "team_id": 1,
      "team_name": "Manchester City",
      "played_games": 30,
      "won": 20,
      "draw": 5,
      "lost": 5,
      "points": 65,
      "goals_for": 60,
      "goals_against": 25,
      "goal_difference": 35
    }
  ],
  "ingestion_timestamp": "2026-04-03T10:30:00+00:00"
}
```

## Error Scenarios Handled

1. **Invalid Competition**: 404 from Football API
2. **Authentication Failure**: 403 with "External API error"
3. **Rate Limiting**: 429 status passed through
4. **Network Issues**: 500 with error details logged
5. **API Structure Changes**: KeyError exceptions caught

## Data Flow Architecture

```
Client Request → FastAPI Router → Football API → JSON Parsing
       ↓              ↓              ↓              ↓
   Path Parameter  URL Construction  Auth Headers  Data Extraction
       ↓              ↓              ↓              ↓
   Schema Mapping ← Field Validation ← Pydantic Models ← List Comprehension
       ↓              ↓              ↓              ↓
   HTTP Response ← Error Handling ← Exception Catching ← Validation Errors
```

## Key Design Principles

### 1. **Data Structure Mapping**
- **API → Schema**: Transforms nested API JSON to flat, validated structures
- **Field Aliases**: Maps camelCase API fields to snake_case Python
- **Type Safety**: Ensures all fields have correct data types

### 2. **Error Resilience**
- **HTTP Error Handling**: Proper status code propagation
- **Exception Isolation**: Catches and logs errors without crashing
- **Graceful Degradation**: Returns structured errors to clients

### 3. **Performance Optimization**
- **Async Operations**: Non-blocking HTTP calls
- **Timeout Protection**: Prevents hanging requests
- **Efficient Parsing**: Single JSON parse operation

### 4. **Maintainability**
- **Modular Design**: Router can be easily extended
- **Configuration-Driven**: All URLs and auth from settings
- **Clear Documentation**: Well-commented data mapping

### 5. **Data Quality**
- **Pydantic Validation**: Ensures data consistency
- **Safe Access**: Uses `.get()` for optional API fields
- **Default Values**: Provides fallbacks for missing data

## Integration with Analytics Pipeline

The standings endpoint feeds league table data into the analytics pipeline:

1. **API Call**: Fetches current standings from Football-Data.org
2. **Data Mapping**: Transforms nested JSON to structured records
3. **Validation**: Pydantic ensures data quality and types
4. **Response**: Returns structured data for BI tools
5. **Kafka Publishing**: Data sent to standings topic
6. **S3 Storage**: Persisted with date partitioning
7. **Snowflake Loading**: Ingested into data warehouse
8. **dbt Processing**: Transformed into mart tables for dashboards

## Testing the Endpoint

```python
# Test successful response
def test_get_standings_success():
    response = client.get("/standings/PL")
    assert response.status_code == 200
    data = response.json()
    assert data["competition_code"] == "PL"
    assert "table" in data
    assert len(data["table"]) > 0

# Test team standing structure
def test_team_standing_structure():
    response = client.get("/standings/PL")
    team = response.json()["table"][0]
    required_fields = ["position", "team_id", "team_name", "points"]
    for field in required_fields:
        assert field in team

# Test error handling
def test_invalid_competition():
    response = client.get("/standings/INVALID")
    assert response.status_code == 404
```

## Schema Validation Benefits

**Before Mapping (Raw API)**:
```json
{
  "standings": [{
    "table": [{
      "position": 1,
      "team": {"id": 1, "name": "Manchester City  "},  // Extra spaces
      "playedGames": 30,
      "goalsFor": 60,
      "goalsAgainst": 25
    }]
  }]
}
```

**After Mapping (Validated Schema)**:
```json
{
  "competition_code": "PL",
  "season_year": 2024,
  "table": [{
    "position": 1,
    "team_id": 1,
    "team_name": "Manchester City",  // Cleaned
    "played_games": 30,
    "goals_for": 60,
    "goals_against": 25,
    "goal_difference": 35  // Calculated
  }]
}
```

This standings.py router provides the "slow-moving fundamentals" data that complements the matches data, giving a complete picture of league performance for analytics and BI dashboards.</content>
<parameter name="filePath">d:\ironhack\Python Code\Projects\capstone_2\STANDINGS_ROUTER_DOCUMENTATION.md