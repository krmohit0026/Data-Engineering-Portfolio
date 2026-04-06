import logging
from confluent_kafka import Producer, Consumer
from Ingestion.football_api.core.config import settings

logger = logging.getLogger(__name__)

def get_kafka_config():
    """
    Constructs the base security configuration for Confluent Cloud.
    """
    return {
        'bootstrap.servers': settings.kafka_bootstrap_servers,
        'security.protocol': settings.kafka_security_protocol,
        'sasl.mechanisms': settings.kafka_sasl_mechanism,
        'sasl.username': settings.kafka_api_key,
        'sasl.password': settings.kafka_api_secret,
    }

def delivery_report(err, msg):
    """
    Callback called once for each message sent to indicate delivery result.
    """
    if err is not None:
        logger.error(f"❌ Message delivery failed: {err}")
    else:
        # Successful delivery to one of your 3 partitions
        logger.info(f"✅ Delivered to {msg.topic()} [Partition: {msg.partition()}]")

def create_producer():
    """
    Creates an Idempotent Producer.
    This is the 'Gold Standard' for preventing duplicate data.
    """
    conf = get_kafka_config()
    conf.update({
        'client.id': f"{settings.app_name}-producer",
        
        # --- IDEMPOTENCE & RELIABILITY ---
        'enable.idempotence': True,      # Prevents duplicate messages if a retry occurs
        'acks': 'all',                   # Wait for all replicas to acknowledge (max persistence)
        'retries': 5,                    # Automatically retry on transient network errors
        'max.in.flight.requests.per.connection': 5,
        
        # Compression saves money on Confluent Cloud data transfer costs
        'compression.type': 'snappy'
    })
    return Producer(conf)

def create_consumer(group_id: str):
    """
    Creates a Consumer designed for reliable 'At Least Once' delivery.
    """
    conf = get_kafka_config()
    conf.update({
        'group.id': group_id,
        'auto.offset.reset': 'earliest', # Start from the beginning if no offset exists
        'enable.auto.commit': True,      # Automatically tell Kafka we read the message
        'session.timeout.ms': 45000,     # Heartbeat timeout for cloud stability
    })
    return Consumer(conf)