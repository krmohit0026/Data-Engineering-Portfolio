# FastAPI Main Application Documentation: main.py

## Overview
This file (`main.py`) is the entry point for the FootballStream Ingestion API. It creates a FastAPI application that serves as the central hub for football data ingestion, with built-in health checks, pre-flight validation, and API endpoints.

## Code Breakdown - Line by Line

### 1. Import Statements
```python
import logging
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Internal Imports
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.routers import matches, standings
from Ingestion.football_api.models.schemas import MatchRecord
```

**Line 1: `import logging`**
- **Purpose**: Imports Python's built-in logging module
- **Usage**: Used for setting up application logging (lines 12-16)
- **Importance**: Essential for debugging, monitoring, and troubleshooting production issues
- **Why needed**: Without logging, you'd have no visibility into application behavior

**Line 2: `import httpx`**
- **Purpose**: Imports the HTTPX library for making HTTP requests
- **Usage**: Used in the startup event for API connectivity testing (line 32)
- **Importance**: Modern async HTTP client, better than requests for async operations
- **Why needed**: Required for testing Football API connectivity during startup

**Line 3: `from fastapi import FastAPI`**
- **Purpose**: Imports the main FastAPI class
- **Usage**: Creates the FastAPI application instance (lines 18-22)
- **Importance**: Core framework for building the REST API
- **Why needed**: This is the heart of your web application

**Line 4: `from fastapi.responses import JSONResponse`**
- **Purpose**: Imports JSONResponse class for custom responses
- **Usage**: Not directly used in this file, but imported for potential future use
- **Importance**: Allows custom JSON response formatting
- **Why needed**: Provides flexibility for response customization

**Lines 6-8: Internal Imports**
```python
# Internal Imports
from Ingestion.football_api.core.config import settings
from Ingestion.football_api.routers import matches, standings
from Ingestion.football_api.models.schemas import MatchRecord
```

**`from Ingestion.football_api.core.config import settings`**
- **Purpose**: Imports the global settings singleton
- **Usage**: Used throughout the file for configuration values
- **Importance**: Provides access to all environment variables and validated settings
- **Why needed**: Centralized configuration management

**`from Ingestion.football_api.routers import matches, standings`**
- **Purpose**: Imports the API router modules
- **Usage**: Registered with the FastAPI app (lines 25-26)
- **Importance**: Contains the actual API endpoints for matches and standings
- **Why needed**: Modular API design - routes are separated into logical modules

**`from Ingestion.football_api.models.schemas import MatchRecord`**
- **Purpose**: Imports Pydantic models for data validation
- **Usage**: Not directly used in main.py, but ensures models are loaded
- **Importance**: Data validation and serialization
- **Why needed**: Ensures type safety for API data structures

### 2. Logging Configuration
```python
# 1. Setup Logging - Crucial for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)
```

**Comment**: `# 1. Setup Logging - Crucial for debugging`
- **Purpose**: Documents the importance of logging
- **Why important**: Logging is critical for production applications

**`logging.basicConfig(...)`**
- **Purpose**: Configures the root logger for the application
- **Parameters**:
  - `level=logging.INFO`: Sets minimum log level to INFO (shows INFO, WARNING, ERROR, CRITICAL)
  - `format="%(asctime)s | %(levelname)s | %(message)s"`: Defines log message format
- **Importance**: Ensures consistent logging across the entire application
- **Why needed**: Without this, logs would be inconsistent or missing

**`logger = logging.getLogger(__name__)`**
- **Purpose**: Creates a logger specific to this module
- **Usage**: Used throughout the file for logging messages
- **Importance**: Allows filtering logs by module and proper log hierarchy
- **Why needed**: Best practice for modular logging

### 3. FastAPI Application Creation
```python
app = FastAPI(
    title=settings.app_name,
    description="Bulletproof Ingestion API for Football Data",
    version="1.0.0"
)
```

**`app = FastAPI(...)`**
- **Purpose**: Creates the main FastAPI application instance
- **Parameters**:
  - `title=settings.app_name`: Uses configured app name (from .env)
  - `description="Bulletproof Ingestion API for Football Data"`: API description for docs
  - `version="1.0.0"`: API version for documentation
- **Importance**: This is the core application object that handles all requests
- **Why needed**: Entry point for the entire web application

### 4. Router Registration
```python
# 2. Register Routers (Both must be here!)
app.include_router(matches.router)
app.include_router(standings.router)
```

**Comment**: `# 2. Register Routers (Both must be here!)`
- **Purpose**: Emphasizes that both routers must be registered
- **Why important**: Without registration, the endpoints won't be available

**`app.include_router(matches.router)`**
- **Purpose**: Registers the matches router with the FastAPI app
- **Effect**: Makes all match-related endpoints available (e.g., `/api/v1/matches`)
- **Importance**: Enables the core functionality of fetching match data
- **Why needed**: Modular API design - keeps routes organized

**`app.include_router(standings.router)`**
- **Purpose**: Registers the standings router with the FastAPI app
- **Effect**: Makes all standings-related endpoints available (e.g., `/api/v1/standings`)
- **Importance**: Enables league standings functionality
- **Why needed**: Completes the API by providing both data types

### 5. Startup Event Handler
```python
# 3. PRE-FLIGHT CHECKS (The Failsafes)
@app.on_event("startup")
async def startup_event():
```

**Decorator**: `@app.on_event("startup")`
- **Purpose**: Registers a function to run when the application starts
- **Trigger**: Executes automatically when `uvicorn` starts the server
- **Importance**: Performs critical validation before accepting requests
- **Why needed**: "Fail fast" principle - catch configuration issues early

**Function Definition**: `async def startup_event():`
- **Async**: Allows for async HTTP calls during startup
- **Name**: `startup_event` is the conventional name for startup handlers
- **Purpose**: Contains all pre-flight validation logic

#### Startup Event Docstring
```python
"""
Runs automatically when the server starts.
If any check fails, the API will log a CRITICAL error.
"""
```
- **Purpose**: Documents what the function does and its behavior
- **Importance**: Clear documentation for maintenance and debugging

#### Check A: Football API Connectivity
```python
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
```

**Pre-flight Header**: `logger.info(f"--- Starting {settings.app_name} Pre-Flight Checks ---")`
- **Purpose**: Logs the start of validation checks
- **Importance**: Clear audit trail of startup process

**Check A Comment**: `# Check A: Football API Connectivity & Authentication`
- **Purpose**: Documents what this validation checks
- **Why important**: Critical dependency that must work

**`async with httpx.AsyncClient() as client:`**
- **Purpose**: Creates an async HTTP client context manager
- **Benefits**: Automatic cleanup, proper resource management
- **Why needed**: Best practice for HTTP client usage

**Test URL Construction**: `test_url = f"{settings.football_base_url}/competitions"`
- **Purpose**: Builds the URL for testing API connectivity
- **Endpoint**: `/competitions` is a basic endpoint that doesn't require specific IDs
- **Why needed**: Simple endpoint to test basic connectivity

**Headers**: `headers = {"X-Auth-Token": settings.football_api_key}`
- **Purpose**: Sets the authentication header required by Football-Data.org API
- **Format**: Uses "X-Auth-Token" as specified in the API documentation
- **Why needed**: API requires authentication for all requests

**HTTP Request**: `response = await client.get(test_url, headers=headers, timeout=5.0)`
- **Method**: GET request to test endpoint
- **Timeout**: 5 seconds to prevent hanging during startup
- **Async**: Uses await for non-blocking execution

**Response Validation**:
- **200**: Success - API is reachable and token is valid
- **403**: Forbidden - Invalid or restricted token
- **Other**: Warning for unexpected status codes
- **Exception**: Catches network errors, DNS issues, etc.

#### Check B: Environment Variables
```python
# Check B: Environment Variables Check
logger.info(f"✅ SUCCESS: Loaded {len(settings.competitions)} competitions from .env.")
logger.info(f"--- Pre-Flight Checks Complete ---")
```

**Check B**: `# Check B: Environment Variables Check`
- **Purpose**: Validates that configuration was loaded properly
- **Why important**: Ensures .env file was parsed correctly

**Competitions Check**: `logger.info(f"✅ SUCCESS: Loaded {len(settings.competitions)} competitions from .env.")`
- **Purpose**: Confirms competitions list was loaded
- **Logic**: Counts items in the competitions list
- **Why needed**: Validates that the most important config is working

**Completion Message**: `logger.info(f"--- Pre-Flight Checks Complete ---")`
- **Purpose**: Marks the end of startup validation
- **Importance**: Clear audit trail completion

### 6. Health Check Endpoints
```python
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
```

**Decorator**: `@app.get("/health", tags=["System"])`
- **Purpose**: Creates a GET endpoint at `/health`
- **Tags**: Groups this endpoint under "System" in API documentation
- **Why needed**: Standard health check endpoint for monitoring

**Function**: `async def health_check():`
- **Purpose**: Returns current application health status
- **Async**: Required for FastAPI async endpoints
- **Return**: JSON object with health information

**Response Structure**:
- `"status": "healthy"`: Indicates the service is running
- `"app": settings.app_name`: Shows configured application name
- `"configurations"`: Object containing key config values
  - `poll_interval`: Shows polling frequency
  - `monitored_leagues`: Lists configured competitions

**Importance**: Used by load balancers, monitoring systems, and deployment platforms

### 7. Root Endpoint
```python
@app.get("/", tags=["System"])
async def root():
    return {
        "message": "FootballStream Ingestion API is running.",
        "docs": "/docs",
        "health": "/health"
    }
```

**Decorator**: `@app.get("/", tags=["System"])`
- **Purpose**: Creates a GET endpoint at the root path `/`
- **Tags**: Groups under "System" in documentation
- **Why needed**: Standard root endpoint for basic service discovery

**Function**: `async def root():`
- **Purpose**: Provides basic API information and navigation
- **Return**: JSON with welcome message and useful links

**Response Structure**:
- `"message"`: Welcome message confirming service is running
- `"docs"`: Link to auto-generated API documentation (`/docs`)
- `"health"`: Link to health check endpoint (`/health`)

**Importance**: Helps developers and systems discover available endpoints

## Application Flow & Importance

### Startup Sequence
1. **Import Phase**: All dependencies loaded
2. **Logging Setup**: Logging configured before any operations
3. **App Creation**: FastAPI application instantiated
4. **Router Registration**: API endpoints made available
5. **Pre-flight Checks**: Critical validation performed
6. **Server Ready**: Application ready to accept requests

### Why Each Component is Critical

#### Logging (Lines 12-16)
- **Without logging**: No visibility into application behavior
- **Production requirement**: Essential for debugging issues
- **Monitoring**: Required for observability

#### Pre-flight Checks (Lines 28-54)
- **Fail Fast Principle**: Catch configuration errors before serving requests
- **Dependency Validation**: Ensure external APIs are accessible
- **Security**: Validate authentication works
- **Reliability**: Prevent runtime failures due to misconfiguration

#### Health Check Endpoint (Lines 57-66)
- **Monitoring**: Load balancers check this endpoint
- **Deployment**: Kubernetes/Docker health checks
- **Operations**: DevOps teams monitor service health
- **Debugging**: Quick way to verify service status

#### Router Registration (Lines 25-26)
- **Functionality**: Without routers, no API endpoints exist
- **Modularity**: Keeps code organized and maintainable
- **Scalability**: Easy to add new features

## API Documentation Access

When running the application, you can access:

- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)
- **Health Check**: `http://localhost:8000/health`
- **Root Info**: `http://localhost:8000/`

## Running the Application

```bash
# Activate virtual environment
source fmenv/Scripts/activate

# Run with uvicorn
uvicorn Ingestion.football_api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the configured port
uvicorn Ingestion.football_api.main:app --reload --host 0.0.0.0 --port $API_PORT
```

## Key Design Principles Demonstrated

1. **Fail Fast**: Pre-flight checks catch issues at startup
2. **Observability**: Comprehensive logging and health checks
3. **Modularity**: Routers separate concerns
4. **Configuration**: Centralized settings management
5. **Documentation**: Self-documenting API with OpenAPI
6. **Error Handling**: Graceful failure with clear error messages
7. **Async/Await**: Modern Python async patterns
8. **Type Safety**: Pydantic models for data validation

## Dependencies & Requirements

- **FastAPI**: Web framework
- **httpx**: Async HTTP client
- **uvicorn**: ASGI server
- **Internal modules**: config, routers, schemas

This main.py file serves as the robust foundation for your football data ingestion API, ensuring reliability, observability, and maintainability.</content>
<parameter name="filePath">d:\ironhack\Python Code\Projects\capstone_2\MAIN_PY_DOCUMENTATION.md