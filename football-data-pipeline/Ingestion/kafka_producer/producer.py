import time
import json
import logging
import httpx
from typing import Dict, Optional, List
from Shared.kafka_utils import create_producer, delivery_report
from Ingestion.football_api.core.config import settings

# 1. Advanced Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class FootballProducer:
    def __init__(self):
        # Failsafe: Initialize Kafka Producer via Shared utils
        self.producer = create_producer()
        self.base_api_url = f"http://localhost:{settings.api_port}"
        
        # Failsafe: Local caches to prevent redundant data costs in Confluent Cloud
        self.last_match_state: Dict[int, str] = {}
        self.last_standing_state: Dict[str, str] = {}

    def fetch_from_local_api(self, endpoint: str, comp_code: str) -> Optional[Dict]:
        """
        Calls our FastAPI wrapper (matches or standings).
        Includes a retry loop for robustness.
        """
        url = f"{self.base_api_url}/{endpoint}/{comp_code}"
        for attempt in range(3):
            try:
                with httpx.Client() as client:
                    response = client.get(url, timeout=15.0)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt + 1}: API {endpoint} unreachable for {comp_code}. Retrying...")
                time.sleep(2)
        
        logger.error(f"CRITICAL: Failed to fetch {endpoint} for {comp_code} after 3 attempts.")
        return None

    def process_matches(self, comp_code: str):
        """Fetches matches and pushes changes to Kafka."""
        data = self.fetch_from_local_api("matches", comp_code)
        if not data: 
            return

        for match in data:
            # FIX 1: Use 'id' instead of 'match_id' (matches your schema)
            m_id = match.get('id')
            if not m_id: 
                continue

            # FIX 2: Updated key names to match your MatchRecord schema
            # home_team and away_team instead of score fields for the fingerprint
            current_state = f"{match.get('status')}_{match.get('home_score')}-{match.get('away_score')}"
            
            # OPTIONAL: To force a backfill, you can temporarily comment out these 2 lines:
            # if self.last_match_state.get(m_id) == current_state:
            #     continue 

            self.producer.produce(
                topic=settings.kafka_topic_matches,
                key=str(m_id), 
                value=json.dumps(match).encode('utf-8'),
                on_delivery=delivery_report
            )
            self.last_match_state[m_id] = current_state

    def process_standings(self, comp_code: str):
        """Fetches league tables and pushes to Kafka."""
        data = self.fetch_from_local_api("standings", comp_code)
        if not data: return

        # Fingerprint: Use the hash of the table to see if positions changed
        # We use the raw string of the table to detect any movement
        current_state = str(data.get('table'))
        if self.last_standing_state.get(comp_code) == hash(current_state):
            return

        self.producer.produce(
            topic=settings.kafka_topic_standings,
            key=comp_code,
            value=json.dumps(data).encode('utf-8'),
            on_delivery=delivery_report
        )
        self.last_standing_state[comp_code] = hash(current_state)

    def run(self):
        """Main execution loop."""
        logger.info(f"🚀 Starting FootballProducer. Monitoring: {settings.competitions}")
        
        try:
            while True:
                for comp in settings.competitions:
                    # 1. Handle Matches (Fast moving)
                    self.process_matches(comp)
                    
                    # 2. Handle Standings (Slow moving)
                    self.process_standings(comp)

                # Flush after every full cycle of leagues
                self.producer.flush(timeout=5.0)
                
                logger.info(f"Cycle complete. Sleeping {settings.poll_interval_seconds}s...")
                time.sleep(settings.poll_interval_seconds)

        except KeyboardInterrupt:
            logger.info("Producer stopped by user.")
        finally:
            logger.info("Flushing final messages...")
            self.producer.flush(timeout=10.0)

if __name__ == "__main__":
    fp = FootballProducer()
    fp.run()