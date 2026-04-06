# Configuration File Documentation: config.py

## Overview
This file (`config.py`) contains the centralized configuration management for the FootballStream ingestion API. It uses Pydantic for type validation and environment variable loading, ensuring robust and secure configuration handling.

## Code Breakdown - Line by Line

### 1. Import Statements
```python
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
```

**Line 1: `import os`**
- **Purpose**: Imports Python's built-in `os` module
- **Usage**: Used later for debugging (line 87) to show current working directory
- **Why needed**: Required for file system operations and environment detection

**Line 2: `from typing import List, Optional`**
- **Purpose**: Imports type hints from Python's typing module
- **Usage**:
  - `List[str]`: Used for `competitions` field (list of competition codes)
  - `Optional[str]`: Used for optional fields like `kafka_api_key` and `kafka_api_secret`
- **Why needed**: Enables static type checking and better IDE support

**Line 3: `from pydantic_settings import BaseSettings, SettingsConfigDict`**
- **Purpose**: Imports Pydantic Settings classes
- **Usage**:
  - `BaseSettings`: Base class for our `Settings` class
  - `SettingsConfigDict`: Configuration dictionary for Pydantic settings
- **Why needed**: Enables automatic loading of environment variables from `.env` file

**Line 4: `from pydantic import field_validator, model_validator`**
- **Purpose**: Imports Pydantic validation decorators
- **Usage**:
  - `@field_validator`: Validates individual fields
  - `@model_validator`: Validates the entire model after all fields are set
- **Why needed**: Provides "bulletproof" validation logic for configuration

### 2. Class Definition
```python
class Settings(BaseSettings):
    """
    Final 'Full-Proof' Configuration for FootballStream.
    Combines API Guardrails with Confluent Cloud Managed Security.
    """
```

**Class Declaration**: `class Settings(BaseSettings):`
- **Inheritance**: Inherits from `BaseSettings` (Pydantic)
- **Purpose**: Creates a configuration class that automatically loads from environment variables
- **Benefits**: Type safety, validation, automatic parsing

**Docstring**: The multi-line comment explains the class purpose
- **"Full-Proof"**: Indicates robust validation and error handling
- **"API Guardrails"**: Refers to validation that prevents API abuse
- **"Confluent Cloud Managed Security"**: Refers to secure Kafka configuration

### 3. Configuration Sections

#### Section 1: Football API Configuration
```python
# 1. FOOTBALL API CONFIGURATION
football_api_key: str
football_base_url: str = "https://api.football-data.org/v4"

# Selection logic (Replaces Stock Tickers/Intervals)
competitions: List[str] = ["PL", "CL", "BL1", "SA", "PD"]
football_season: int = 2024
```

**`football_api_key: str`**
- **Type**: Required string (no default value)
- **Purpose**: Authentication token for Football-Data.org API
- **Validation**: Has a custom validator (see below)
- **Source**: Environment variable `FOOTBALL_API_KEY`

**`football_base_url: str = "https://api.football-data.org/v4"`**
- **Type**: String with default value
- **Purpose**: Base URL for the football API
- **Default**: Official Football-Data.org API v4 endpoint
- **Override**: Can be changed via `FOOTBALL_BASE_URL` env var

**`competitions: List[str] = ["PL", "CL", "BL1", "SA", "PD"]`**
- **Type**: List of strings with default values
- **Purpose**: Competition codes to monitor
- **Defaults**: Premier League (PL), Champions League (CL), Bundesliga (BL1), Serie A (SA), La Liga (PD)
- **Validation**: Has a custom validator (see below)
- **Source**: Environment variable `COMPETITIONS` (comma-separated)

**`football_season: int = 2024`**
- **Type**: Integer with default value
- **Purpose**: Season year for data collection
- **Default**: 2024 season
- **Source**: Environment variable `FOOTBALL_SEASON`

#### Section 2: Kafka Configuration
```python
# 2. MANAGED KAFKA (CONFLUENT CLOUD) CONFIGURATION
kafka_bootstrap_servers: str = "localhost:9092"
kafka_api_key: Optional[str] = None      # Confluent API Key
kafka_api_secret: Optional[str] = None   # Confluent API Secret
kafka_security_protocol: str = "SASL_SSL"
kafka_sasl_mechanism: str = "PLAIN"
```

**`kafka_bootstrap_servers: str = "localhost:9092"`**
- **Type**: String with default value
- **Purpose**: Kafka broker addresses
- **Default**: Local Kafka on port 9092
- **Cloud**: For Confluent Cloud, would be something like `pkc-xxxxx.us-east-1.provider.confluent.cloud:9092`
- **Source**: Environment variable `KAFKA_BOOTSTRAP_SERVERS`

**`kafka_api_key: Optional[str] = None`**
- **Type**: Optional string (can be None)
- **Purpose**: Confluent Cloud API key for authentication
- **Default**: None (for local Kafka)
- **Required**: When using Confluent Cloud
- **Source**: Environment variable `KAFKA_API_KEY`

**`kafka_api_secret: Optional[str] = None`**
- **Type**: Optional string (can be None)
- **Purpose**: Confluent Cloud API secret for authentication
- **Default**: None (for local Kafka)
- **Required**: When using Confluent Cloud
- **Source**: Environment variable `KAFKA_API_SECRET`

**`kafka_security_protocol: str = "SASL_SSL"`**
- **Type**: String with default value
- **Purpose**: Security protocol for Kafka connection
- **Default**: SASL_SSL (secure authentication)
- **Local**: Would be "PLAINTEXT" for local unsecured Kafka
- **Source**: Environment variable `KAFKA_SECURITY_PROTOCOL`

**`kafka_sasl_mechanism: str = "PLAIN"`**
- **Type**: String with default value
- **Purpose**: SASL authentication mechanism
- **Default**: PLAIN (username/password authentication)
- **Source**: Environment variable `KAFKA_SASL_MECHANISM`

#### Section 3: Kafka Topics
```python
# 3. KAFKA TOPICS (Updated to match your Cloud environment)
kafka_topic_matches: str = "matches"
kafka_topic_standings: str = "STANDINGS"  # Matches your Confluent UI
kafka_topic_errors: str = "errors"
```

**`kafka_topic_matches: str = "matches"`**
- **Type**: String with default value
- **Purpose**: Kafka topic name for match data
- **Default**: "matches"
- **Source**: Environment variable `KAFKA_TOPIC_MATCHES`

**`kafka_topic_standings: str = "STANDINGS"`**
- **Type**: String with default value
- **Purpose**: Kafka topic name for league standings data
- **Default**: "STANDINGS" (note: uppercase to match Confluent UI)
- **Source**: Environment variable `KAFKA_TOPIC_STANDINGS`

**`kafka_topic_errors: str = "errors"`**
- **Type**: String with default value
- **Purpose**: Kafka topic name for error messages
- **Default**: "errors"
- **Source**: Environment variable `KAFKA_TOPIC_ERRORS`

#### Section 4: Operational Settings
```python
# 4. OPERATIONAL SETTINGS
poll_interval_seconds: int = 60
app_name: str = "FootballStream-Ingestion-API"
api_port: int = 8000
s3_bucket_name: str = "ironhack-capstone-2"
```

**`poll_interval_seconds: int = 60`**
- **Type**: Integer with default value
- **Purpose**: How often to poll the football API (in seconds)
- **Default**: 60 seconds (1 minute)
- **Validation**: Has a custom validator (minimum 10 seconds)
- **Source**: Environment variable `POLL_INTERVAL_SECONDS`

**`app_name: str = "FootballStream-Ingestion-API"`**
- **Type**: String with default value
- **Purpose**: Application name for logging and identification
- **Default**: "FootballStream-Ingestion-API"
- **Source**: Environment variable `APP_NAME`

**`api_port: int = 8000`**
- **Type**: Integer with default value
- **Purpose**: Port number for the FastAPI server
- **Default**: 8000 (standard development port)
- **Source**: Environment variable `API_PORT`

**`s3_bucket_name: str = "ironhack-capstone-2"`**
- **Type**: String with default value
- **Purpose**: AWS S3 bucket name for data storage
- **Default**: "ironhack-capstone-2"
- **Source**: Environment variable `S3_BUCKET_NAME`

### 4. Field Validators (Individual Field Validation)

#### API Key Validator
```python
@field_validator("football_api_key")
@classmethod
def check_api_key_exists(cls, v: str) -> str:
    if not v or v == "your_actual_token_here":
        raise ValueError("CRITICAL: FOOTBALL_API_KEY is missing in .env!")
    return v
```

**Decorator**: `@field_validator("football_api_key")`
- **Purpose**: Validates the `football_api_key` field specifically
- **Trigger**: Runs whenever `football_api_key` is set

**Decorator**: `@classmethod`
- **Purpose**: Makes this a class method (doesn't need instance)
- **Convention**: Required for Pydantic field validators

**Parameters**: `cls, v: str`
- `cls`: The class (Settings)
- `v`: The value being validated (string)

**Logic**:
- `if not v`: Checks if value is empty/None
- `or v == "your_actual_token_here"`: Checks for placeholder text
- `raise ValueError(...)`: Throws error with clear message
- `return v`: Returns validated value

**Purpose**: Prevents deployment with missing or placeholder API keys

#### Competitions Validator
```python
@field_validator("competitions")
@classmethod
def validate_competitions(cls, v: List[str]) -> List[str]:
    # Ensures only codes supported by the API Free Tier are used
    supported_codes = [
        "WC", "CL", "BL1", "DED", "BSA", "PD", "FL1", "ELC", "PPL", "EC", "SA", "PL"
    ]
    unsupported = [code for code in v if code not in supported_codes]
    if unsupported:
        raise ValueError(f"Unsupported Competition Codes: {unsupported}. Check your .env!")
    return v
```

**Purpose**: Ensures only supported competition codes are used

**Supported Codes**:
- WC: World Cup
- CL: Champions League
- BL1: Bundesliga
- DED: Eredivisie
- BSA: Campeonato Brasileiro
- PD: La Liga
- FL1: Ligue 1
- ELC: Europa League
- PPL: Primeira Liga
- EC: European Championship
- SA: Serie A
- PL: Premier League

**Logic**:
- Creates list of unsupported codes
- Raises error if any unsupported codes found
- Returns validated list

#### Poll Interval Validator
```python
@field_validator("poll_interval_seconds")
@classmethod
def check_rate_limit(cls, v: int) -> int:
    # Prevents being banned by the API for polling too fast
    if v < 10:
        raise ValueError("Rate Limit Warning: Poll interval must be >= 10 seconds.")
    return v
```

**Purpose**: Prevents API rate limit violations

**Logic**:
- Checks if interval is less than 10 seconds
- Raises error if too aggressive
- Football-Data.org API has rate limits

### 5. Model Validator (Whole Model Validation)
```python
@model_validator(mode='after')
def check_kafka_cloud_auth(self) -> 'Settings':
    """
    Final check: If we are pointing to Confluent Cloud, 
    ensure we actually have credentials loaded.
    """
    if "confluent.cloud" in self.kafka_bootstrap_servers:
        if not self.kafka_api_key or not self.kafka_api_secret:
            raise ValueError(
                "Cloud Kafka detected: KAFKA_API_KEY and KAFKA_API_SECRET "
                "are required in your .env file!"
            )
    return self
```

**Decorator**: `@model_validator(mode='after')`
- **Purpose**: Validates the entire model after all fields are processed
- **Mode**: 'after' means it runs after individual field validators

**Method**: `def check_kafka_cloud_auth(self) -> 'Settings':`
- **Instance method**: Has access to `self` (the Settings instance)
- **Return type**: Returns the Settings instance

**Logic**:
- Checks if bootstrap servers contain "confluent.cloud"
- If using Confluent Cloud, ensures API key and secret are provided
- Raises error if credentials missing for cloud Kafka
- Returns self to continue

### 6. Model Configuration
```python
# 5. Pydantic Model Configuration
model_config = SettingsConfigDict(
    env_file=".env", 
    env_file_encoding='utf-8',
    extra="ignore"
)
```

**`model_config`**: Special Pydantic configuration attribute

**`env_file=".env"`**: Tells Pydantic to load from `.env` file

**`env_file_encoding='utf-8'`**: Specifies UTF-8 encoding for the env file

**`extra="ignore"`**: Ignores extra environment variables not defined in the class

### 7. Debug Statement
```python
import os
print(f"DEBUG: Looking for .env in: {os.getcwd()}")
```

**Purpose**: Debug output to show where the script is looking for `.env`

**`import os`**: Re-imports os (already imported above, but explicit here)

**`os.getcwd()`**: Gets current working directory

**`print(f"...")`**: Prints debug message with directory path

**Note**: This helps troubleshoot `.env` file location issues

### 8. Singleton Instance
```python
# Singleton instance
settings = Settings()
```

**Purpose**: Creates a single global instance of the Settings class

**Benefits**:
- **Singleton Pattern**: Only one instance exists
- **Global Access**: Import `settings` from this module anywhere
- **Lazy Loading**: Only loads when first imported
- **Validation**: All validation runs when instance is created

**Usage**: `from config import settings` in other modules

## Environment Variables Mapping

| Environment Variable | Class Field | Required | Default |
|---------------------|-------------|----------|---------|
| `FOOTBALL_API_KEY` | `football_api_key` | Yes | - |
| `FOOTBALL_BASE_URL` | `football_base_url` | No | `https://api.football-data.org/v4` |
| `COMPETITIONS` | `competitions` | No | `["PL", "CL", "BL1", "SA", "PD"]` |
| `FOOTBALL_SEASON` | `football_season` | No | `2024` |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka_bootstrap_servers` | No | `localhost:9092` |
| `KAFKA_API_KEY` | `kafka_api_key` | No* | `None` |
| `KAFKA_API_SECRET` | `kafka_api_secret` | No* | `None` |
| `KAFKA_SECURITY_PROTOCOL` | `kafka_security_protocol` | No | `SASL_SSL` |
| `KAFKA_SASL_MECHANISM` | `kafka_sasl_mechanism` | No | `PLAIN` |
| `KAFKA_TOPIC_MATCHES` | `kafka_topic_matches` | No | `matches` |
| `KAFKA_TOPIC_STANDINGS` | `kafka_topic_standings` | No | `STANDINGS` |
| `KAFKA_TOPIC_ERRORS` | `kafka_topic_errors` | No | `errors` |
| `POLL_INTERVAL_SECONDS` | `poll_interval_seconds` | No | `60` |
| `APP_NAME` | `app_name` | No | `FootballStream-Ingestion-API` |
| `API_PORT` | `api_port` | No | `8000` |
| `S3_BUCKET_NAME` | `s3_bucket_name` | No | `ironhack-capstone-2` |

*Required when using Confluent Cloud

## Example .env File

```env
# Football API
FOOTBALL_API_KEY=your_actual_api_key_here
FOOTBALL_BASE_URL=https://api.football-data.org/v4
COMPETITIONS=PL,CL,BL1,SA,PD
FOOTBALL_SEASON=2024

# Kafka (Local Development)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT
KAFKA_SASL_MECHANISM=PLAIN

# Kafka (Confluent Cloud Production)
# KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.provider.confluent.cloud:9092
# KAFKA_API_KEY=your_confluent_api_key
# KAFKA_API_SECRET=your_confluent_api_secret
# KAFKA_SECURITY_PROTOCOL=SASL_SSL

# Topics
KAFKA_TOPIC_MATCHES=matches
KAFKA_TOPIC_STANDINGS=STANDINGS
KAFKA_TOPIC_ERRORS=errors

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=ironhack-capstone-2

# Application
POLL_INTERVAL_SECONDS=60
API_PORT=8000
APP_NAME=FootballStream-Ingestion-API
```

## Key Design Principles

1. **Fail Fast**: Validation catches configuration errors at startup
2. **Secure by Default**: No sensitive defaults, explicit credential requirements
3. **Environment Agnostic**: Works for local development and cloud production
4. **Type Safety**: Full type hints and Pydantic validation
5. **Clear Error Messages**: Descriptive validation errors for easy debugging
6. **Singleton Pattern**: Single configuration instance across the application

## Usage in Other Modules

```python
# In any other Python file
from Ingestion.football_api.core.config import settings

# Access configuration
api_key = settings.football_api_key
topics = [settings.kafka_topic_matches, settings.kafka_topic_standings]
poll_interval = settings.poll_interval_seconds
```

This configuration system ensures your application is robust, secure, and easy to deploy across different environments.</content>
<parameter name="filePath">d:\ironhack\Python Code\Projects\capstone_2\CONFIG_DOCUMENTATION.md