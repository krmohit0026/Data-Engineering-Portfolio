import json
import logging
import boto3
import os
import time
from datetime import datetime, timezone
from Shared.kafka_utils import create_consumer
from Ingestion.football_api.core.config import settings

# 1. Setup Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class S3Consumer:
    def __init__(self):
        # Initialize Kafka Consumer and subscribe to BOTH topics from settings
        self.consumer = create_consumer(group_id="football-s3-ingest-group")
        self.topics = [settings.kafka_topic_matches, settings.kafka_topic_standings]
        self.consumer.subscribe(self.topics)
        
        # --- UPDATED: EXPLICIT AWS CREDENTIALS ---
        # This forces Boto3 to use the keys from your .env file
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        self.bucket_name = settings.s3_bucket_name 
        # ----------------------------------------

    def format_s3_path(self, topic_name: str) -> str:
        """
        Creates a Hive-partitioned path structure.
        Example: raw/matches/year=2026/month=04/day=01/data_211251.json
        """
        now = datetime.now(timezone.utc)
        # We extract the 'type' (matches or standings) from the topic name
        folder_type = "matches" if "match" in topic_name.lower() else "standings"
        
        return (
            f"raw/{folder_type}/"
            f"year={now.year}/"
            f"month={now.strftime('%m')}/"
            f"day={now.strftime('%d')}/"
            f"data_{now.strftime('%H%M%S')}.json"
        )

    def upload_to_s3(self, batch: list, topic_name: str):
        """
        Final-Proof Upload: Saves a batch of data to S3 based on its topic.
        """
        if not batch:
            return

        s_path = self.format_s3_path(topic_name)
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s_path,
                Body=json.dumps(batch, indent=2),
                ContentType='application/json'
            )
            logger.info(f"✅ Archived {len(batch)} records from {topic_name} to S3 -> {s_path}")
        except Exception as e:
            logger.error(f"❌ S3 Upload Failed: {e}")

    def run(self):
        """
        The Main Loop: Listens to Kafka and batches data to reduce S3 costs.
        """
        logger.info(f"🚀 S3 Consumer is LIVE. Listening to topics: {self.topics}")
        
        # We maintain separate batches for matches and standings to keep S3 clean
        batches = {
            settings.kafka_topic_matches: [],
            settings.kafka_topic_standings: []
        }
        last_upload_time = time.time()

        try:
            while True:
                msg = self.consumer.poll(1.0)

                # Timer-based flush: If 30 seconds pass, upload everything we have
                if msg is None:
                    if time.time() - last_upload_time > 30:
                        for t_name, b_data in batches.items():
                            if b_data:
                                self.upload_to_s3(b_data, t_name)
                                batches[t_name] = []
                        last_upload_time = time.time()
                    continue

                if msg.error():
                    logger.error(f"Kafka Error: {msg.error()}")
                    continue

                # Identify which topic the message came from
                current_topic = msg.topic()
                
                try:
                    payload = json.loads(msg.value().decode('utf-8'))
                    batches[current_topic].append(payload)
                except Exception as e:
                    logger.warning(f"Skipping malformed JSON from {current_topic}: {e}")

                # Batching Guardrail: Upload if a specific topic batch hits 10 records
                if len(batches[current_topic]) >= 10:
                    self.upload_to_s3(batches[current_topic], current_topic)
                    batches[current_topic] = []
                    last_upload_time = time.time()

        except KeyboardInterrupt:
            logger.info("Consumer stopping gracefully...")
        finally:
            # Flush remaining data in all batches before exiting
            for t_name, b_data in batches.items():
                if b_data:
                    self.upload_to_s3(b_data, t_name)
            self.consumer.close()

if __name__ == "__main__":
    ingestor = S3Consumer()
    ingestor.run()