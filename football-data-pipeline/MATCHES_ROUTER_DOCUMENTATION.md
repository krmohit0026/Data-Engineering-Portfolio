# FastAPI Matches Router Documentation: matches.py

## Overview
This file (`matches.py`) implements the matches endpoint for the FootballStream API. It fetches football match data from the external Football-Data.org API, processes and validates the data, and returns it in a consistent format for downstream processing.

## Code Breakdown - Line by Line

### 1. Import Statements
```python
import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

# --- FIXED ABSOLUTE IMPORTS ---
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.models.schemas import MatchRecord
```

**Line 1: `import logging`**
- **Purpose**: Imports Python's logging module
- **Usage**: Used throughout for error tracking and debugging
- **Importance**: Essential for monitoring API calls and troubleshooting issues
- **Why needed**: External API calls require comprehensive logging

**Line 2: `import httpx`**
- **Purpose**: Imports the HTTPX async HTTP client
- **Usage**: Makes async HTTP requests to the Football API
- **Importance**: Modern async client for non-blocking API calls
- **Why needed**: FastAPI is async, so HTTP client must also be async

**Line 3: FastAPI Components**
```python
from fastapi import APIRouter, HTTPException, Query
```

**`APIRouter`**
- **Purpose**: Creates modular router for match endpoints
- **Usage**: Groups match-related routes under `/matches` prefix
- **Importance**: Modular API design, keeps code organized
- **Why needed**: Separates concerns from main app

**`HTTPException`**
- **Purpose**: Raises HTTP errors with proper status codes
- **Usage**: Returns 429 for rate limits, 500 for server errors
- **Importance**: Proper error responses for API consumers
- **Why needed**: External API failures need to be communicated clearly

**`Query`**
- **Purpose**: Defines query parameters for endpoints
- **Usage**: Optional status filter parameter
- **Importance**: Type-safe query parameter handling
- **Why needed**: Allows filtering matches by status

**Line 4: Type Hints**
```python
from typing import List, Optional
```

**`List`**
- **Purpose**: Type hint for list of MatchRecord objects
- **Usage**: Return type annotation for the endpoint
- **Importance**: Type safety for API responses
- **Why needed**: Ensures response structure is predictable

**`Optional`**
- **Purpose**: Type hint for optional values
- **Usage**: Optional status query parameter
- **Importance**: Explicit nullable parameter handling
- **Why needed**: Query parameters can be omitted

**Lines 6-7: Internal Imports**
```python
# --- FIXED ABSOLUTE IMPORTS ---
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.models.schemas import MatchRecord
```

**`settings`**
- **Purpose**: Imports the global configuration singleton
- **Usage**: Accesses API keys, URLs, seasons, etc.
- **Importance**: Centralized configuration management
- **Why needed**: All API parameters come from validated config

**`MatchRecord`**
- **Purpose**: Imports the Pydantic schema for match data
- **Usage**: Validates and structures match data
- **Importance**: Ensures data consistency and type safety
- **Why needed**: "Bulletproof" data validation before returning

### 2. Logging Setup
```python
# Set up logging so we can see what's happening in the console
logger = logging.getLogger(__name__)
```

**Purpose**: Creates a logger specific to this module
- **Module-specific**: `__name__` makes logs identifiable by file
- **Hierarchy**: Inherits from root logger configuration
- **Usage**: All logging calls use this logger instance
- **Importance**: Proper log categorization and filtering

### 3. Router Creation
```python
router = APIRouter(
    prefix="/matches",
    tags=["Matches"]
)
```

**`APIRouter()`**: Creates a modular router instance
- **Prefix**: All routes will be under `/matches`
- **Tags**: Groups endpoints in API documentation under "Matches"
- **Modularity**: Can be imported and registered in main.py
- **Organization**: Keeps match logic separate from other endpoints

### 4. Endpoint Definition
```python
@router.get("/{competition_code}", response_model=List[MatchRecord])
async def get_matches(
    competition_code: str,
    # CHANGE: Set default to "FINISHED" so it backfills when no query is sent
    status: Optional[str] = Query("FINISHED", description="Filter by status: SCHEDULED, LIVE, FINISHED")
):
```

**Decorator**: `@router.get("/{competition_code}", response_model=List[MatchRecord])`
- **HTTP Method**: GET request
- **Path Parameter**: `{competition_code}` (e.g., "PL", "CL")
- **Response Model**: Returns list of validated MatchRecord objects
- **Type Safety**: FastAPI auto-validates response against schema

**Function Parameters**:
- **`competition_code: str`**: Path parameter for league code
- **`status: Optional[str]`**: Query parameter with default "FINISHED"
- **`Query(...)`**: FastAPI query parameter with description

**Default Status**: `"FINISHED"`
- **Purpose**: Backfills historical data by default
- **Why needed**: Most use cases want completed matches
- **Override**: Can be changed via `?status=SCHEDULED`

### 5. Function Docstring
```python
"""
Fetches matches for a specific competition and flattens them 
into our bulletproof MatchRecord schema.
"""
```

**Purpose**: Documents what the function does
- **"Fetches matches"**: Calls external API
- **"Flattens them"**: Converts nested API response to flat structure
- **"Bulletproof schema"**: References Pydantic validation
- **Importance**: Clear documentation for API consumers

### 6. Request Preparation
```python
# 1. Prepare the Request
url = f"{settings.football_base_url}/competitions/{competition_code}/matches"
headers = {"X-Auth-Token": settings.football_api_key}

# Ensure we use the current season from settings
params = {"season": settings.football_season}

# This will now use "FINISHED" by default
if status:
    params["status"] = status.upper()
```

**URL Construction**: `url = f"{settings.football_base_url}/competitions/{competition_code}/matches"`
- **Dynamic**: Uses configured base URL and path parameter
- **Endpoint**: Football API matches endpoint for specific competition
- **Example**: `https://api.football-data.org/v4/competitions/PL/matches`

**Headers**: `headers = {"X-Auth-Token": settings.football_api_key}`
- **Authentication**: Required by Football-Data.org API
- **Format**: "X-Auth-Token" header as per API documentation
- **Security**: Uses validated API key from configuration

**Base Parameters**: `params = {"season": settings.football_season}`
- **Season**: Uses configured season year (e.g., 2024)
- **Filtering**: Limits results to current season
- **Consistency**: Same season across all requests

**Status Parameter**: `if status: params["status"] = status.upper()`
- **Conditional**: Only adds if status is provided
- **Uppercase**: Normalizes to API expectations
- **Default**: Uses "FINISHED" if no status specified

### 7. API Call with Error Handling
```python
# 2. Call the External API safely
try:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=10.0)
        
        if response.status_code == 429:
            logger.error("API Rate Limit Hit!")
            raise HTTPException(status_code=429, detail="Football API Rate Limit reached.")
        
        response.raise_for_status()
        data = response.json()
```

**Try Block**: Comprehensive error handling for external API calls

**HTTP Client**: `async with httpx.AsyncClient() as client:`
- **Context Manager**: Automatic cleanup of connections
- **Async**: Non-blocking HTTP requests
- **Best Practice**: Proper resource management

**API Request**: `response = await client.get(url, headers=headers, params=params, timeout=10.0)`
- **Method**: GET request to Football API
- **Parameters**: Headers (auth), params (season/status), timeout (10 seconds)
- **Timeout**: Prevents hanging on slow/unresponsive API

**Rate Limit Check**: `if response.status_code == 429:`
- **Specific Handling**: 429 = Too Many Requests
- **Logging**: Records rate limit hits for monitoring
- **User Feedback**: Clear error message about rate limiting

**General Error Check**: `response.raise_for_status()`
- **Automatic**: Raises exception for 4xx/5xx status codes
- **Convenience**: Single line handles most HTTP errors
- **Consistency**: Standard HTTP error handling

**Data Extraction**: `data = response.json()`
- **JSON Parsing**: Converts response to Python dict
- **Assumption**: API returns valid JSON
- **Efficiency**: Parses once, uses throughout function

### 8. Exception Handling
```python
except httpx.HTTPStatusError as e:
    logger.error(f"API Error: {e.response.status_code} for {competition_code}")
    raise HTTPException(status_code=e.response.status_code, detail="Error fetching data")
except Exception as e:
    logger.info(f"Unexpected Connection Error: {e}")
    raise HTTPException(status_code=500, detail="Could not connect to Football API")
```

**HTTPStatusError**: Specific handling for HTTP errors (4xx, 5xx)
- **Logging**: Records status code and competition for debugging
- **Propagation**: Raises FastAPI HTTPException with same status
- **User Context**: Provides meaningful error message

**Generic Exception**: Catches network errors, timeouts, etc.
- **Logging**: Records unexpected errors (info level)
- **Fallback**: Returns 500 Internal Server Error
- **Safety**: Never exposes internal error details to users

### 9. Data Processing
```python
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
```

**Data Extraction**: `raw_matches = data.get("matches", [])`
- **Safe Access**: Uses `.get()` to handle missing "matches" key
- **Default**: Empty list if no matches found
- **Robustness**: Handles API response variations

**Processing Loop**: `for match in raw_matches:`
- **Iteration**: Processes each match individually
- **Isolation**: Errors in one match don't affect others
- **Efficiency**: Builds list of validated records

**Score Extraction**: `score_data = match.get("score", {}).get("fullTime", {})`
- **Nested Access**: Safely navigates nested JSON structure
- **Defaults**: Empty dict if score/fullTime missing
- **Safety**: Prevents KeyError exceptions

**Schema Creation**: `MatchRecord(...)`
- **Validation**: Pydantic validates all fields
- **Transformation**: Applies field aliases and validators
- **Type Safety**: Ensures consistent data types

**Field Mapping**:
- **API → Schema**: Maps nested API fields to flat schema
- **Defaults**: "Unknown" for missing team names
- **Null Handling**: Schema validators handle None values

**Error Handling**: `except Exception as schema_err:`
- **Isolation**: Skips corrupted records instead of failing entirely
- **Logging**: Warns about data quality issues
- **Continuation**: Processes remaining valid records

**Return**: `return records`
- **Type**: List[MatchRecord] as per response_model
- **Validated**: All records passed Pydantic validation
- **Consistent**: Same structure for all API consumers

## API Usage Examples

### Get Finished Matches (Default)
```bash
GET /matches/PL
# Returns all finished Premier League matches for current season
```

### Get Scheduled Matches
```bash
GET /matches/PL?status=SCHEDULED
# Returns upcoming Premier League matches
```

### Get Live Matches
```bash
GET /matches/CL?status=LIVE
# Returns currently playing Champions League matches
```

## Error Scenarios Handled

1. **Rate Limiting**: 429 status with clear error message
2. **Authentication Failure**: 403 status from API
3. **Network Issues**: 500 with generic error message
4. **Invalid Competition**: 404 from Football API
5. **Corrupted Data**: Skips bad records, processes valid ones
6. **API Timeout**: 10-second timeout prevents hanging

## Data Flow Architecture

```
Client Request → FastAPI Router → External API Call → JSON Response
       ↓              ↓              ↓              ↓
   Validation    Error Handling   Data Extraction  Schema Validation
       ↓              ↓              ↓              ↓
   HTTP Response ← Error Response ← Record Creation ← Pydantic Models
```

## Key Design Principles

### 1. **Fail-Safe Design**
- **Error Isolation**: One bad record doesn't break the entire response
- **Graceful Degradation**: Returns partial data when possible
- **Clear Error Messages**: Users understand what went wrong

### 2. **Type Safety**
- **Pydantic Validation**: Ensures data structure consistency
- **Response Models**: FastAPI validates return data
- **Type Hints**: IDE support and runtime checking

### 3. **Observability**
- **Comprehensive Logging**: Tracks all operations and errors
- **Request Context**: Logs include competition codes and parameters
- **Error Categorization**: Different log levels for different error types

### 4. **Performance**
- **Async Operations**: Non-blocking HTTP calls
- **Timeout Protection**: Prevents resource exhaustion
- **Efficient Processing**: Minimal data transformations

### 5. **Maintainability**
- **Modular Design**: Router can be easily extended
- **Configuration-Driven**: All URLs and parameters from config
- **Clear Separation**: API calls, processing, and validation separated

## Testing the Endpoint

```python
# Test successful response
def test_get_matches_success():
    response = client.get("/matches/PL")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check schema compliance
    match = data[0]
    assert "match_id" in match
    assert "status" in match

# Test error handling
def test_get_matches_invalid_competition():
    response = client.get("/matches/INVALID")
    assert response.status_code == 404

# Test rate limiting
def test_rate_limit_handling():
    # Mock API to return 429
    response = client.get("/matches/PL")
    assert response.status_code == 429
    assert "Rate Limit" in response.json()["detail"]
```

## Integration with Kafka Pipeline

The endpoint feeds into the larger data pipeline:

1. **API Call**: Fetches data from Football-Data.org
2. **Validation**: Pydantic ensures data quality
3. **Response**: Returns structured data to client
4. **Client Processing**: Data sent to Kafka topics
5. **Storage**: Persisted to S3 with partitioning
6. **Warehouse**: Loaded into Snowflake
7. **Transformation**: Processed by dbt models

This matches.py router is the critical "ingestion point" that ensures high-quality, validated football data enters your entire analytics pipeline.</content>
<parameter name="filePath">d:\ironhack\Python Code\Projects\capstone_2\MATCHES_ROUTER_DOCUMENTATION.md