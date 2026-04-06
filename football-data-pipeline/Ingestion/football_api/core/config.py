import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator

class Settings(BaseSettings):
    """
    Final 'Full-Proof' Configuration for FootballStream.
    Combines API Guardrails with Confluent Cloud Managed Security.
    """
    
    # 1. FOOTBALL API CONFIGURATION
    football_api_key: str
    football_base_url: str = "https://api.football-data.org/v4"
    
    # Selection logic (Replaces Stock Tickers/Intervals)
    competitions: List[str] = ["PL", "CL", "BL1", "SA", "PD"]
    football_season: int = 2024
    
    # 2. MANAGED KAFKA (CONFLUENT CLOUD) CONFIGURATION
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_api_key: Optional[str] = None      # Confluent API Key
    kafka_api_secret: Optional[str] = None   # Confluent API Secret
    kafka_security_protocol: str = "SASL_SSL"
    kafka_sasl_mechanism: str = "PLAIN"
    
    # 3. KAFKA TOPICS (Updated to match your Cloud environment)
    kafka_topic_matches: str = "matches"
    kafka_topic_standings: str = "STANDINGS"  # Matches your Confluent UI
    kafka_topic_errors: str = "errors"
    
    # 4. OPERATIONAL SETTINGS
    poll_interval_seconds: int = 60
    app_name: str = "FootballStream-Ingestion-API"
    api_port: int = 8000
    s3_bucket_name: str = "ironhack-capstone-2"
    # --- FAILSAFE GUARDRAILS (The 'Bulletproof' Logic) ---

    @field_validator("football_api_key")
    @classmethod
    def check_api_key_exists(cls, v: str) -> str:
        if not v or v == "your_actual_token_here":
            raise ValueError("CRITICAL: FOOTBALL_API_KEY is missing in .env!")
        return v

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

    @field_validator("poll_interval_seconds")
    @classmethod
    def check_rate_limit(cls, v: int) -> int:
        # Prevents being banned by the API for polling too fast
        if v < 10:
            raise ValueError("Rate Limit Warning: Poll interval must be >= 10 seconds.")
        return v

   # Remove the old @field_validator("kafka_bootstrap_servers") block entirely
    
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

    # 5. Pydantic Model Configuration
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra="ignore"
    )

import os
print(f"DEBUG: Looking for .env in: {os.getcwd()}")

# Singleton instance
settings = Settings()