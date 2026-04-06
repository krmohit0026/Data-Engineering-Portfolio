# Football Data Pipeline - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Prerequisites & Setup](#prerequisites--setup)
5. [Configuration](#configuration)
6. [Data Flow](#data-flow)
7. [Pushing Data to S3](#pushing-data-to-s3)
8. [Pulling Data from S3 to Snowflake](#pulling-data-from-s3-to-snowflake)
9. [dbt Transformation Pipeline](#dbt-transformation-pipeline)
10. [Running the Pipeline](#running-the-pipeline)
11. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---
## 📖 Detailed Code Documentation
For a deep dive into specific components of this pipeline, please refer to:
* [Main Ingestion Logic](./MAIN_PY_DOCUMENTATION.md)
* [Data Schemas & Models](./SCHEMAS_DOCUMENTATION.md)
* [Matches Router Logic](./MATCHES_ROUTER_DOCUMENTATION.md)
* [Standings Router Logic](./STANDINGS_ROUTER_DOCUMENTATION.md)
* [Infrastructure Setup](./CONFIG_DOCUMENTATION.md)
## Project Overview

This is a comprehensive **ELT (Extract, Load, Transform)** pipeline for football data that:
- **Extracts** real-time football data from the Football-Data.org API
- **Loads** data through Kafka streaming to AWS S3 (data lake)
- **Transforms** data using dbt and Snowflake (data warehouse)
- **Exposes** transformed data through Mart tables for BI/Analytics

### Key Technologies
- **API Ingestion**: FastAPI + Football-Data.org API
- **Streaming**: Apache Kafka (Confluent Cloud)
- **Cloud Storage**: AWS S3
- **Data Warehouse**: Snowflake
- **Transformation**: dbt (Data Build Tool)
- **IaC**: Docker Compose for local Kafka

### Monitored Competitions
- **PL** - Premier League (England)
- **CL** - Champions League (UEFA)
- **BL1** - Bundesliga (Germany)
- **SA** - Serie A (Italy)
- **PD** - La Liga (Spain)

---

## Architecture

```
┌──────────────────────────────────┐
│  Football-Data.org API           │
│  (External Data Source)          │
└────────────┬─────────────────────┘
             │
             ↓
┌──────────────────────────────────┐
│  FastAPI Ingestion Service       │
│  (Polling every 60 seconds)      │
│  ├─ /matches endpoint            │
│  ├─ /standings endpoint          │
│  └─ Health checks                │
└────────────┬─────────────────────┘
             │
             ↓
┌──────────────────────────────────┐
│  Apache Kafka Topics             │
│  ├─ matches (topic)              │
│  └─ STANDINGS (topic)            │
└────────────┬─────────────────────┘
             │
          ┌──┴──┐
          ↓     ↓
    ┌─────────────────────┐
    │  Kafka Consumers    │
    │  ├─ S3 Consumer     │
    │  └─ Stream Proc.    │
    └─────────┬───────────┘
              │
              ├─→ AWS S3 Data Lake
              │   ├─ raw/matches/
              │   └─ raw/standings/
              │
              ├─→ Snowflake Staging
              │   ├─ RAW.MATCHES
              │   └─ RAW.STANDINGS
              │
              └─→ dbt Transformation
                  ├─ Staging Layer (views)
                  │  ├─ stg_matches
                  │  └─ stg_standings
                  │
                  ├─ Intermediate Layer (tables)
                  │  ├─ dim_teams
                  │  └─ fct_matches
                  │
                  └─ Mart Layer (tables)
                     ├─ mart_league_standings
                     └─ mart_team_performance
```

---

## Components

### 1. **FastAPI Ingestion Service** (`Ingestion/football_api/`)
Polls the external Football API and publishes data to Kafka.

**Key Files:**
- `main.py` - FastAPI application with health checks
- `routers/matches.py` - Matches data endpoint
- `routers/standings.py` - Standings data endpoint
- `core/config.py` - Configuration management
- `models/schemas.py` - Pydantic data models

**Functionality:**
- Polls Football-Data.org API every 60 seconds
- Validates API responses and authentication
- Publishes to Kafka topics
- Implements pre-flight checks on startup

---

### 2. **Kafka Streaming Layer** (`Shared/`, `Processing/`)
Message broker for decoupling data producers and consumers.

**Configuration:**
- **Bootstrap Servers**: `localhost:9092` (local) or Confluent Cloud
- **Topics**:
  - `matches` - Raw match data
  - `STANDINGS` - League standings data
  - `errors` - Error logs

**Security:**
- Uses `SASL_SSL` for Confluent Cloud
- API Key/Secret authentication
- Idempotent producer (prevents duplicates)

---

### 3. **S3 Data Lake** (`Processing/kafka_consumer/consumer.py`)
Persists raw data with Hive partitioning for cost optimization.

**S3 Structure:**
```
s3://ironhack-capstone-2/
├── raw/matches/year=2026/month=04/day=01/data_*.json
└── raw/standings/year=2026/month=04/day=01/data_*.json
```

**Features:**
- Batches records before uploading (reduces S3 API calls)
- Implements 30-second flush interval
- Partitioned by year/month/day for efficient querying
- JSON format for human readability

---

### 4. **Snowflake Data Warehouse**
Central hub for data storage and transformation.

**Database Structure:**
```
FOOTBALL_DB
├── RAW (schema)
│   ├── MATCHES (table) - Raw match data from S3
│   └── STANDINGS (table) - Raw standings data from S3
│
├── TRANSFORMED (schema)
│   ├── stg_matches (view)
│   ├── stg_standings (view)
│   ├── dim_teams (table)
│   └── fct_matches (table)
│
└── MARTS (schema)
    ├── mart_league_standings (table)
    └── mart_team_performance (table)
```

---

### 5. **dbt Transformation Pipeline** (`dbt_football/`)

#### Staging Layer (`models/staging/`)
- **Purpose**: Lightweight transformations to clean and rename columns
- **Materialization**: Views (no storage cost)
- Models:
  - `stg_matches.sql` - Flattens JSON, renames match columns
  - `stg_standings.sql` - Cleans standings data

**Example (stg_matches.sql):**
```sql
with raw_matches as (
    select * from {{ source('football_raw', 'matches') }}
)
select
    raw_data:id::int as match_id,
    raw_data:competition_code::string as league_code,
    raw_data:season_year::int as season_year,
    raw_data:utcDate::timestamp_tz as match_date,
    raw_data:status::string as match_status,
    raw_data:home_team::string as home_team,
    raw_data:away_team::string as away_team,
    raw_data:home_score::int as home_score,
    raw_data:away_score::int as away_score
from raw_matches
```

#### Intermediate Layer (`models/intermediate/`)
- **Purpose**: Business logic & dimensions
- **Materialization**: Tables (persisted)
- Models:
  - `dim_teams.sql` - Team dimensions with surrogate keys
  - `fct_matches.sql` - Match facts and metrics

**Example (dim_teams.sql):**
```sql
with teams as (
    select distinct 
        team_id, 
        team_name, 
        league_code
    from {{ ref('stg_standings') }}
)
select 
    {{ dbt_utils.generate_surrogate_key(['team_id', 'league_code']) }} as team_pk,
    * 
from teams
```

#### Marts Layer (`models/mart/`)
- **Purpose**: Denormalized tables for BI/Analytics
- **Materialization**: Tables (optimized for queries)
- Models:
  - `mart_league_standings.sql` - Standings with business logic
  - `mart_team_performance.sql` - Team performance metrics

**Example (mart_league_standings.sql):**
```sql
with standings as (
    select * from {{ ref('stg_standings') }}
)
select 
    team_name,
    league_code,
    season_year,
    points,
    position,
    played,
    goal_diff,
    case 
        when position = 1 then 'League Leader'
        when position <= 4 then 'Champions League Spot'
        when position >= 18 then 'Relegation Zone'
        else 'Mid-Table'
    end as league_status
from standings
order by league_code, position
```

---

## Prerequisites & Setup

### Required Software
- Python 3.12+
- Docker & Docker Compose
- git
- AWS Account with S3 bucket
- Snowflake Account
- Confluent Cloud Account (or local Kafka)
- Football-Data.org API Key

### Step 1: Clone & Environment Setup

```bash
# Navigate to project directory
cd d:\ironhack\Python\ Code\Projects\capstone_2

# Create virtual environment
python -m venv fmenv
source fmenv/Scripts/activate  # Windows: fmenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create Environment File

Create `.env` file in the project root:

```env
# ===== FOOTBALL API =====
FOOTBALL_API_KEY=your_actual_token_here
FOOTBALL_BASE_URL=https://api.football-data.org/v4
COMPETITIONS=PL,CL,BL1,SA,PD
FOOTBALL_SEASON=2024

# ===== KAFKA (Confluent Cloud) =====
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.provider.confluent.cloud:9092
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_API_KEY=your_confluent_api_key
KAFKA_API_SECRET=your_confluent_api_secret
KAFKA_TOPIC_MATCHES=matches
KAFKA_TOPIC_STANDINGS=STANDINGS
KAFKA_TOPIC_ERRORS=errors

# ===== AWS S3 =====
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=ironhack-capstone-2

# ===== SNOWFLAKE =====
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=your_snowflake_user
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=FOOTBALL_DB
SNOWFLAKE_SCHEMA=RAW

# ===== API SERVER =====
API_PORT=8000
POLL_INTERVAL_SECONDS=60
```

### Step 3: Start Kafka (Local Development)

```bash
# Navigate to Infrastructure folder
cd Infrastructure

# Start Docker Compose (Kafka, Zookeeper, Redpanda Console)
docker-compose up -d

# Verify Kafka is running
docker ps
```

---

## Configuration

### FastAPI Configuration (`Ingestion/football_api/core/config.py`)

The `Settings` class manages all configuration with built-in validation:

```python
class Settings(BaseSettings):
    # API Configuration
    football_api_key: str  # Required
    football_base_url: str = "https://api.football-data.org/v4"
    competitions: List[str] = ["PL", "CL", "BL1", "SA", "PD"]
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_api_key: Optional[str] = None  # For Confluent Cloud
    kafka_api_secret: Optional[str] = None
    
    # S3 Configuration
    s3_bucket_name: str = "ironhack-capstone-2"
    
    # Operational Settings
    poll_interval_seconds: int = 60  # Min: 10 seconds (API rate limit)
    api_port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
```

**Key Validators:**
- `check_api_key_exists`: Prevents missing API keys
- `validate_competitions`: Only allows supported competition codes
- `check_rate_limit`: Prevents API bans (min 10 sec polling)
- `check_kafka_cloud_auth`: Ensures Confluent Cloud credentials

---

## Data Flow

### Phase 1: Data Ingestion → Kafka

```
1. FastAPI polls Football API every 60 seconds
   ├─ GET /competitions/{id}/matches
   └─ GET /competitions/{id}/standings

2. Data Validation:
   ├─ Status code 200 check
   ├─ API auth token validation
   └─ Schema validation (Pydantic models)

3. Publish to Kafka topics:
   ├─ Topic: "matches" → Match data
   └─ Topic: "STANDINGS" → Standings data
```

**Example API Response:**
```json
{
  "id": 12345,
  "utcDate": "2026-04-02T20:00:00Z",
  "status": "FINISHED",
  "homeTeam": {
    "id": 1,
    "name": "Manchester United",
    "crest": "..."
  },
  "awayTeam": {
    "id": 2,
    "name": "Liverpool",
    "crest": "..."
  },
  "score": {
    "fullTime": { "home": 2, "away": 1 }
  }
}
```

### Phase 2: Kafka → S3 Data Lake

The Kafka Consumer (`Processing/kafka_consumer/consumer.py`) batches and uploads data:

```python
class S3Consumer:
    def format_s3_path(self, topic_name: str) -> str:
        # Format: raw/matches/year=2026/month=04/day=01/data_211251.json
        return f"raw/{folder_type}/year={year}/month={month}/day={day}/data_{timestamp}.json"
    
    def upload_to_s3(self, batch: list, topic_name: str):
        # Uploads batch as JSON to S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_path,
            Body=json.dumps(batch, indent=2)
        )
```

**S3 Output Structure:**
```
s3://ironhack-capstone-2/
├── raw/
│   ├── matches/
│   │   └── year=2026/month=04/day=01/
│   │       ├── data_203000.json
│   │       ├── data_203030.json
│   │       └── data_203100.json
│   └── standings/
│       └── year=2026/month=04/day=01/
│           ├── data_203015.json
│           └── data_203045.json
```

**Features:**
- ✅ Batches records (reduces S3 API costs)
- ✅ 30-second flush interval (low latency)
- ✅ Hive partitioning (efficient querying)
- ✅ Error handling & retry logic

---

## Pushing Data to S3

### Manual S3 Upload (Testing)

```python
import boto3
import json
from datetime import datetime, timezone

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id='your_key',
    aws_secret_access_key='your_secret',
    region_name='us-east-1'
)

# Prepare data
sample_data = [
    {
        "id": 12345,
        "homeTeam": "Manchester United",
        "awayTeam": "Liverpool",
        "score": 2,
        "date": "2026-04-02"
    }
]

# Upload to S3
now = datetime.now(timezone.utc)
s3_key = f"raw/matches/year={now.year}/month={now.strftime('%m')}/day={now.strftime('%d')}/data_{now.strftime('%H%M%S')}.json"

s3_client.put_object(
    Bucket='ironhack-capstone-2',
    Key=s3_key,
    Body=json.dumps(sample_data, indent=2),
    ContentType='application/json'
)

print(f"✅ Uploaded to s3://ironhack-capstone-2/{s3_key}")
```

### Through Kafka Consumer (Production)

```bash
# Start the Kafka consumer that automatically uploads to S3
python -m Processing.kafka_consumer.consumer
```

**What Happens:**
1. Consumer polls Kafka topics (`matches`, `STANDINGS`)
2. Accumulates records in memory
3. Every 30 seconds (or when batch size reached):
   - Creates partitioned S3 path
   - Uploads batch as JSON file
   - Logs success/failure
4. Runs indefinitely until interrupted

### S3 Best Practices

- **Partitioning**: Always use `year`, `month`, `day` for efficient querying
- **Batching**: Reduce API calls; flush every 30 seconds
- **Format**: Use JSON for readability; Parquet for analytics
- **Versioning**: Enable S3 versioning for data recovery
- **Lifecycle**: Move old data to Glacier for cost savings

---

## Pulling Data from S3 to Snowflake

### Step 1: Configure Snowflake

Create a Snowflake warehouse user with S3 permissions:

```sql
-- Create warehouse
CREATE WAREHOUSE COMPUTE_WH WITH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- Create database
CREATE DATABASE FOOTBALL_DB;

-- Create raw schema for landed data
CREATE SCHEMA FOOTBALL_DB.RAW;

-- Create stage for S3 integration
CREATE STAGE s3_stage
    URL = 's3://ironhack-capstone-2/raw'
    CREDENTIALS = (AWS_KEY_ID='your_key' AWS_SECRET_KEY='your_secret')
    FILE_FORMAT = (TYPE = 'JSON');
```

### Step 2: Create External Tables

```sql
-- Raw matches table
CREATE OR REPLACE TABLE FOOTBALL_DB.RAW.MATCHES (
    raw_data VARIANT
) AS
SELECT * FROM @s3_stage/matches (
    FILE_FORMAT => 'JSON'
);

-- Raw standings table
CREATE OR REPLACE TABLE FOOTBALL_DB.RAW.STANDINGS (
    raw_data VARIANT
) AS
SELECT * FROM @s3_stage/standings (
    FILE_FORMAT => 'JSON'
);
```

### Step 3: Set Up Snowflake External Volume (Modern Approach)

```sql
-- Create external volume for S3
CREATE EXTERNAL VOLUME s3_football
    STORAGE_LOCATIONS = (
        's3://ironhack-capstone-2/raw/matches',
        's3://ironhack-capstone-2/raw/standings'
    );

-- Create external tables
CREATE TABLE FOOTBALL_DB.RAW.MATCHES (
    raw_data VARIANT
)
    LOCATION = @s3_football/matches
    AUTO_REFRESH = TRUE
    FILE_FORMAT = (TYPE = 'JSON');
```

### Step 4: Load Data via COPY Command

```sql
-- One-time load or scheduled load
COPY INTO FOOTBALL_DB.RAW.MATCHES
FROM @s3_stage/matches
FILE_FORMAT = 'JSON'
ON_ERROR = 'CONTINUE';

-- Schedule daily refresh (using Snowflake Tasks)
CREATE OR REPLACE TASK load_s3_data
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '1 HOUR'
AS
COPY INTO FOOTBALL_DB.RAW.MATCHES
FROM @s3_stage/matches
FILE_FORMAT = 'JSON'
ON_ERROR = 'CONTINUE';

ALTER TASK load_s3_data RESUME;
```

### Step 5: Query Landed Data

```sql
-- Verify data in Snowflake
SELECT COUNT(*) as total_matches FROM FOOTBALL_DB.RAW.MATCHES;

-- Parse JSON and inspect structure
SELECT 
    raw_data:id as match_id,
    raw_data:homeTeam.name as home_team,
    raw_data:awayTeam.name as away_team,
    raw_data:score.fullTime.home as home_score,
    raw_data:score.fullTime.away as away_score
FROM FOOTBALL_DB.RAW.MATCHES
LIMIT 10;
```

### Automation: Pipe for Continuous Loading

```sql
-- Create a pipe for automatic S3 → Snowflake loading
CREATE OR REPLACE PIPE s3_match_pipe
    AUTO_INGEST = TRUE
    AS
    COPY INTO FOOTBALL_DB.RAW.MATCHES
    FROM @s3_stage/matches
    FILE_FORMAT = 'JSON';

-- Monitor pipe
SELECT * FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
    PIPE_NAME=>'s3_match_pipe',
    RESULT_LIMIT => 100
));
```

---

## dbt Transformation Pipeline

### Step 1: Initialize dbt Project

```bash
# Navigate to dbt project
cd dbt_football

# Install dbt packages and dependencies
dbt deps

# Create profiles.yml for Snowflake connection
dbt debug  # Tests connection
```

### Step 2: Configure dbt Profile

Create `~/.dbt/profiles.yml`:

```yaml
dbt_football:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: xy12345.us-east-1  # Snowflake account ID
      user: your_snowflake_user
      password: your_snowflake_password
      role: TRANSFORMER
      database: FOOTBALL_DB
      schema: TRANSFORMED
      warehouse: COMPUTE_WH
      threads: 4
      client_session_keep_alive: False
      query_tag: dbt_football_dev

    prod:
      type: snowflake
      account: xy12345.us-east-1
      user: prod_user
      password: prod_password
      role: TRANSFORMER_PROD
      database: FOOTBALL_DB
      schema: MARTS
      warehouse: COMPUTE_WH_PROD
      threads: 8
```

### Step 3: Define Sources

File: `models/staging/_sources.yml`

```yaml
version: 2

sources:
  - name: football_raw
    database: FOOTBALL_DB
    schema: RAW
    tables:
      - name: matches
        description: "Raw match data from API via S3"
        columns:
          - name: raw_data
            description: "Raw JSON data from Football-Data.org API"
      
      - name: standings
        description: "Raw standings data from API via S3"
```

### Step 4: Staging Layer Models

File: `models/staging/stg_matches.sql`

```sql
{{ config(
    materialized='view',
    tags=['staging']
) }}

with raw_matches as (
    select * from {{ source('football_raw', 'matches') }}
)

select
    raw_data:id::int as match_id,
    raw_data:competitionCode::string as league_code,
    raw_data:season.year::int as season_year,
    raw_data:utcDate::timestamp_tz as match_date,
    raw_data:status::string as match_status,
    raw_data:homeTeam.id::int as home_team_id,
    raw_data:homeTeam.name::string as home_team,
    raw_data:awayTeam.id::int as away_team_id,
    raw_data:awayTeam.name::string as away_team,
    raw_data:score.fullTime.home::int as home_score,
    raw_data:score.fullTime.away::int as away_score,
    raw_data:score.fullTime.home::int - raw_data:score.fullTime.away::int as score_diff,
    case 
        when raw_data:score.fullTime.home::int > raw_data:score.fullTime.away::int then 'HOME_WIN'
        when raw_data:score.fullTime.home::int < raw_data:score.fullTime.away::int then 'AWAY_WIN'
        else 'DRAW'
    end as match_result,
    current_timestamp as loaded_at
from raw_matches
where raw_data is not null
```

### Step 5: Intermediate Layer Models

File: `models/intermediate/dim_teams.sql`

```sql
{{ config(
    materialized='table',
    unique_id=['team_pk'],
    tags=['intermediate']
) }}

with teams as (
    select distinct 
        team_id, 
        team_name, 
        league_code
    from {{ ref('stg_standings') }}
)

select 
    {{ dbt_utils.generate_surrogate_key(['team_id', 'league_code']) }} as team_pk,
    team_id,
    team_name,
    league_code,
    current_timestamp as created_at
from teams
where team_id is not null
```

File: `models/intermediate/fct_matches.sql`

```sql
{{ config(
    materialized='table',
    tags=['intermediate']
) }}

with matches as (
    select * from {{ ref('stg_matches') }}
),

home_team as (
    select team_pk, team_id from {{ ref('dim_teams') }}
),

away_team as (
    select team_pk, team_id from {{ ref('dim_teams') }}
)

select
    matches.match_id,
    matches.match_date,
    matches.league_code,
    home_team.team_pk as home_team_pk,
    away_team.team_pk as away_team_pk,
    matches.home_score,
    matches.away_score,
    matches.score_diff,
    matches.match_result,
    current_timestamp as processed_at
from matches
left join home_team on matches.home_team_id = home_team.team_id
left join away_team on matches.away_team_id = away_team.team_id
```

### Step 6: Mart Layer Models

File: `models/mart/mart_league_standings.sql`

```sql
{{ config(
    materialized='table',
    grant = {
        'select': ['analyst_role']
    },
    tags=['marts']
) }}

with standings as (
    select * from {{ ref('stg_standings') }}
)

select 
    team_name,
    league_code,
    season_year,
    points,
    position,
    played,
    won,
    drawn,
    lost,
    goals_for,
    goals_against,
    goals_for - goals_against as goal_diff,
    case 
        when position = 1 then 'League Leader'
        when position <= 4 then 'Champions League Spot'
        when position = 5 then 'Europa League Spot'
        when position >= (select max(position) - 3 from standings where league_code = standings.league_code) 
            then 'Relegation Zone'
        else 'Mid-Table'
    end as qualification_status,
    current_timestamp as calculated_at
from standings
order by league_code, season_year, position
```

File: `models/mart/mart_team_performance.sql`

```sql
{{ config(
    materialized='table',
    tags=['marts']
) }}

with match_stats as (
    select
        date_trunc('week', match_date) as week_start,
        home_team,
        count(*) as matches_played,
        sum(case when match_result = 'HOME_WIN' then 3 when match_result = 'DRAW' then 1 else 0 end) as points,
        sum(home_score) as goals_scored,
        sum(away_score) as goals_conceded,
        avg(home_score) as avg_goals_scored,
        avg(away_score) as avg_goals_conceded
    from {{ ref('stg_matches') }}
    group by date_trunc('week', match_date), home_team
)

select
    week_start,
    home_team as team_name,
    matches_played,
    points,
    goals_scored,
    goals_conceded,
    goals_scored - goals_conceded as goal_diff,
    avg_goals_scored,
    avg_goals_conceded,
    round((points / (matches_played * 3)) * 100, 2) as points_per_game_pct,
    current_timestamp as calculated_at
from match_stats
order by week_start desc, points desc
```

### Step 7: Run dbt Models

```bash
# Validate all models syntax
dbt parse

# Run all models in DAG order
dbt run

# Run specific model
dbt run --select stg_matches

# Run with specific tag
dbt run --select tag:marts

# Run upstream and downstream
dbt run --select stg_matches+  # Run stg_matches and all downstream

# Test data quality
dbt test

# Generate documentation
dbt docs generate

# Serve documentation locally
dbt docs serve  # Visit http://localhost:8000
```

### Step 8: dbt Project Configuration

File: `dbt_project.yml`

```yaml
name: 'dbt_football'
version: '1.0.0'
config-version: 2

profile: 'dbt_football'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]
target-path: "target"

clean-targets:
  - "target"
  - "dbt_packages"

models:
  dbt_football:
    staging:
      +materialized: view
      +tags: ['staging']
    
    intermediate:
      +materialized: table
      +tags: ['intermediate']
    
    marts:
      +materialized: table
      +tags: ['marts']
      +grant:
        select: ['analyst_role']
```

---

## Running the Pipeline

### Full Pipeline Execution (Production)

```bash
# Terminal 1: Start Kafka Container
cd Infrastructure
docker-compose up -d

# Terminal 2: Activate virtual environment and start FastAPI
source fmenv/Scripts/activate
python -m Ingestion.football_api.main

# Terminal 3: Start Kafka Consumer (S3 uploader)
source fmenv/Scripts/activate
python -m Processing.kafka_consumer.consumer

# Terminal 4: Run dbt transformations (in a loop or scheduler)
cd dbt_football
dbt run --profiles-dir ~/.dbt/profiles.yml

# Terminal 5: Monitor Kafka topics (optional)
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic matches --from-beginning
```

### Orchestrated Execution (Recommended)

**Using Airflow/Prefect/dbt Cloud:**

```yaml
# Example dbt Cloud job schedule
triggers:
  - name: daily_transformation
    schedule_type: schedule
    schedule:
      day_of_week: null
      hour: 2  # 2 AM UTC
      minute: 0
    timezone: UTC

# Executes dbt model chain daily
models_to_run:
  - stg_matches
  - stg_standings
  - dim_teams
  - fct_matches
  - mart_league_standings
  - mart_team_performance
```

### Local Testing

```bash
# Test single endpoint
curl http://localhost:8000/health

# Test matches data
curl http://localhost:8000/api/v1/matches

# Check API docs
open http://localhost:8000/docs  # Swagger UI
```

---

## Monitoring & Troubleshooting

### Common Issues

#### 1. **Kafka Connection Failed**

```bash
# Check if Kafka is running
docker ps | grep kafka

# View Kafka logs
docker logs <kafka_container_id>

# Restart Kafka
docker-compose restart kafka

# Test connection
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

#### 2. **S3 Upload Failures**

```bash
# Check AWS credentials
aws s3 ls --profile default

# Test S3 bucket access
aws s3 ls s3://ironhack-capstone-2

# Check producer logs
python -m Processing.kafka_consumer.consumer 2>&1 | grep "ERROR"
```

#### 3. **Snowflake Connection Errors**

```bash
# Test Snowflake connection
dbt debug

# Check Snowflake user and role
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();

# Verify S3 stage
SHOW STAGES;

# Test S3 stage access
LIST @s3_stage/matches;
```

#### 4. **dbt Model Failures**

```bash
# Run specific model with debug
dbt run --select stg_matches -d

# Check dbt logs
tail -f logs/dbt.log

# Validate model SQL syntax
dbt parse --select stg_matches

# Full data lineage
dbt docs generate && dbt docs serve
```

### Monitoring Queries

**Snowflake:**
```sql
-- Monitor table growth
SELECT TABLE_NAME, ROW_COUNT, BYTES
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'RAW';

-- Check query history
SELECT QUERY_ID, USER_NAME, START_TIME, EXECUTION_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE DATABASE_NAME = 'FOOTBALL_DB'
ORDER BY START_TIME DESC
LIMIT 10;

-- Monitor warehouse compute
SELECT * 
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE WAREHOUSE_NAME = 'COMPUTE_WH'
ORDER BY START_TIME DESC
LIMIT 20;
```

**Kafka:**
```bash
# List all topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check topic stats
docker exec kafka kafka-topics --describe --bootstrap-server localhost:9092 --topic matches

# Monitor consumer lag
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group football-s3-ingest-group --describe
```

### Performance Optimization

1. **Kafka Batching**: Increase batch size in `consumer.py` to reduce S3 calls
2. **Snowflake Clustering**: Add clustering keys to large tables
3. **dbt Materialization**: Use `incremental` for fact tables
4. **S3 Partitioning**: Always partition by date for faster queries
5. **Query Caching**: Enable result caching in Snowflake

### Data Quality Checks

```sql
-- dbt tests in models/staging/stg_matches.yml
tests:
  - not_null:
      column_name: match_id
  - unique:
      column_name: match_id
  - relationships:
      column_name: home_team_id
      to: ref('dim_teams')
      field: team_id
```

---

## Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `pip install -r requirements.txt` | Install dependencies |
| `docker-compose up -d` | Start Kafka container |
| `dbt run` | Execute all models |
| `dbt test` | Run data tests |
| `dbt docs generate` | Generate documentation |
| `dbt freshness` | Check source freshness |
| `aws s3 ls s3://bucket` | List S3 files |
| `curl http://localhost:8000/health` | Test API health |

---

## Additional Resources

- [Football-Data.org API Docs](https://www.football-data.org/documentation/api)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/BestPractices.html)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)

---

## Support & Contribution

For issues or questions:
1. Check logs: `logs/dbt.log`, Docker container logs
2. Review `.env` configuration
3. Test individual components (API, Kafka, S3, Snowflake)
4. Check connection strings and credentials

---

**Last Updated**: April 2, 2026  
**Project Version**: 1.0.0  
**Status**: Production Ready
