"""
config.py — FluxCart Kafka Pipeline Configuration
==================================================

PURPOSE:
    Single source of truth for every Kafka setting used across the pipeline.
    Every other file imports from here — producer.py, setup_topics.py,
    analytics.py, fraud.py, inventory.py all import this file.

WHY THIS EXISTS AS A SEPARATE FILE:
    In a real pipeline, you never hardcode Kafka addresses or topic names
    in multiple places. If your Kafka cluster moves to a new server, you
    change ONE line here and every component picks it up automatically.
    If a topic is renamed, you change it here — not in 5 different files.

TEACHING NOTE:
    Read this file carefully before writing any other file.
    Every tuning knob for producers and consumers is explained here.
    Understanding these settings is understanding how Kafka behaves.
"""


# =============================================================================
# BROKER CONNECTION
# =============================================================================

# KAFKA_BOOTSTRAP_SERVERS:
#   The address(es) your Python code uses to first connect to the Kafka cluster.
#   You only need ONE broker address here — Kafka will automatically tell your
#   code about all other brokers once the first connection is made.
#
#   We list broker-1 as the entry point (localhost:9092).
#   After connecting, Kafka returns metadata about all 3 brokers automatically.
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092,localhost:9093,localhost:9094"


# =============================================================================
# TOPIC NAMES
# =============================================================================
# All topic names defined as constants in one place.
# Import these constants instead of typing the string directly.
#
# WHY CONSTANTS INSTEAD OF STRINGS?
#   If you type "fluxcart.user.behavior" in 5 files and make a typo in one,
#   your producer writes to one topic and your consumer reads from another.
#   You get no error — just silent data loss. Constants catch this at import time.
#
# NAMING CONVENTION: "domain.entity.eventtype"
#   fluxcart          = the platform/domain
#   user/orders/payments = the entity this topic is about
#   behavior/events   = the type of events in this topic

TOPIC_USER_BEHAVIOR   = "fluxcart.user.behavior"    # browse, search, add-to-cart events
TOPIC_ORDERS          = "fluxcart.orders"            # order lifecycle events
TOPIC_PAYMENTS        = "fluxcart.payments"          # payment lifecycle events
TOPIC_FRAUD_ALERTS    = "fluxcart.fraud.alerts"      # fraud detections (written by fraud consumer)
TOPIC_DEAD_LETTER     = "fluxcart.dead.letter"       # unprocessable events from any consumer


# =============================================================================
# TOPIC CONFIGURATION
# =============================================================================
# Each topic has specific partition and retention requirements based on:
#   - Expected volume (higher volume = more partitions)
#   - Business/legal retention requirements (payments = longer)
#   - Consumer parallelism needs (more partitions = more consumers possible)
#
# This dictionary is used by setup_topics.py to create topics with the
# correct settings. Keys are topic names, values are configuration dicts.

TOPIC_CONFIGS = {

    TOPIC_USER_BEHAVIOR: {
        # 6 partitions: highest volume topic — every browse, search, scroll.
        # 6 partitions means up to 6 analytics consumer instances can run
        # in parallel, each reading 1 partition.
        "num_partitions": 6,

        # Replication factor 3: one copy on each broker.
        # Survives one broker going down without losing any browse data.
        "replication_factor": 3,

        # 30 days retention: browse data older than a month has low value.
        # Calculated as: 30 days x 24 hours x 60 min x 60 sec x 1000 ms
        "retention_ms": 30 * 24 * 60 * 60 * 1000,   # 2,592,000,000 ms
    },

    TOPIC_ORDERS: {
        # 3 partitions: lower volume than browse events.
        # Not every browse leads to an order — typical conversion is 2-5%.
        "num_partitions": 3,

        "replication_factor": 3,

        # 90 days retention: order history has operational and legal value.
        # Customer service references recent orders.
        # Financial reporting looks back across quarters.
        "retention_ms": 90 * 24 * 60 * 60 * 1000,   # 7,776,000,000 ms
    },

    TOPIC_PAYMENTS: {
        # 3 partitions: even lower volume than orders.
        # Payment volume approximately equals order volume.
        "num_partitions": 3,

        "replication_factor": 3,

        # 90 days: payment records are financial records.
        # Regulatory requirement — must be kept for auditing.
        "retention_ms": 90 * 24 * 60 * 60 * 1000,
    },

    TOPIC_FRAUD_ALERTS: {
        # 1 partition: fraud alerts are low volume (rare events).
        # Single partition guarantees strict ordering of alerts.
        # You want to process alert #1 before alert #2 — always.
        "num_partitions": 1,

        "replication_factor": 3,

        # 30 days: alerts are investigated and resolved within days/weeks.
        "retention_ms": 30 * 24 * 60 * 60 * 1000,
    },

    TOPIC_DEAD_LETTER: {
        # 1 partition: dead letter events are rare (malformed messages).
        # Single partition makes them easy to inspect in order.
        "num_partitions": 1,

        "replication_factor": 3,

        # 30 days: gives engineers enough time to investigate and fix
        # the bad events, then replay them if needed.
        "retention_ms": 30 * 24 * 60 * 60 * 1000,
    },
}


# =============================================================================
# PRODUCER CONFIGURATION
# =============================================================================
# Used by producer.py and by the fraud consumer (which also produces alerts).
#
# These settings control the trade-off between:
#   SPEED      <- how fast messages are sent
#   SAFETY     <- how sure we are messages are not lost
#   THROUGHPUT <- how many messages per second we can sustain

PRODUCER_CONFIG = {

    # bootstrap.servers: where to connect first.
    # After this, Kafka tells the producer about all other brokers.
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,

    # client.id: a human-readable name for this producer.
    # Shows up in Kafka logs and monitoring tools.
    # Makes debugging easier — you can see which producer sent what.
    "client.id": "fluxcart-event-simulator",

    # -------------------------------------------------------------------------
    # ACKNOWLEDGMENT MODE — the most important producer setting
    # -------------------------------------------------------------------------
    # acks controls when the broker tells the producer "I have your message".
    #
    # "0" = fire and forget
    #       Producer sends and moves on immediately. No waiting.
    #       FASTEST. Can lose messages if broker crashes right after receiving.
    #       Use for: metrics, logs — where losing one event occasionally is fine.
    #
    # "1" = leader acknowledgment
    #       Producer waits for the partition LEADER to write the message.
    #       FAST. Small risk: if leader crashes before replicating, message lost.
    #       Use for: most application events where occasional loss is acceptable.
    #
    # "all" = all in-sync replicas must acknowledge
    #       Producer waits until ALL ISR brokers have written the message.
    #       SAFEST. Slowest of the three. No message is ever lost.
    #       Use for: payments, orders — anything where loss is unacceptable.
    #
    # We use "all" for FluxCart because order and payment events cannot be lost.
    "acks": "all",

    # -------------------------------------------------------------------------
    # RETRY CONFIGURATION
    # -------------------------------------------------------------------------
    # retries: how many times to retry a failed send before giving up.
    # Network hiccups, broker restarts, leader elections — all cause transient
    # failures. Retrying handles these automatically.
    "retries": 5,

    # retry.backoff.ms: how long to wait between retries (milliseconds).
    # 300ms means: try -> fail -> wait 300ms -> try -> fail -> wait 300ms...
    # Gives the broker time to recover before the next attempt.
    "retry.backoff.ms": 300,

    # -------------------------------------------------------------------------
    # BATCHING — how the producer groups messages before sending
    # -------------------------------------------------------------------------
    # Instead of sending one message at a time (inefficient), the producer
    # buffers messages in memory and sends them in batches.
    # More batching = fewer network trips = higher throughput.
    # Less batching = lower latency = faster individual message delivery.

    # linger.ms: how long the producer WAITS to accumulate a batch.
    # 20ms means: "wait up to 20ms for more messages before sending."
    # If 1000 messages arrive in 20ms, they go in one batch — one network trip.
    # If only 1 message arrives in 20ms, it gets sent anyway after the wait.
    # Set to 0 for minimum latency (sends immediately, no waiting).
    "linger.ms": 20,

    # batch.size: maximum size of one batch in bytes (32KB here).
    # If the batch fills up before linger.ms elapses, it sends immediately.
    # Larger batch = better throughput, higher memory usage.
    # 32768 bytes = 32KB — a reasonable default for most use cases.
    "batch.size": 32768,

    # -------------------------------------------------------------------------
    # COMPRESSION
    # -------------------------------------------------------------------------
    # compression.type: compress batches before sending over the network.
    # Reduces network bandwidth and broker disk usage significantly.
    #
    # Options:
    #   "none"   -> no compression, fastest CPU, most network/disk
    #   "gzip"   -> best compression ratio, slowest CPU
    #   "snappy" -> good compression, fast CPU — Google's algorithm
    #   "lz4"    -> fastest compression/decompression, slightly less ratio
    #   "zstd"   -> best overall ratio+speed tradeoff (newest option)
    #
    # "snappy" is a good default — reasonable compression with low CPU overhead.
    "compression.type": "snappy",

    # -------------------------------------------------------------------------
    # IDEMPOTENCE — preventing duplicate messages
    # -------------------------------------------------------------------------
    # enable.idempotence: when True, Kafka assigns each message a sequence number.
    # If the producer retries a message (thinking it failed), but it actually
    # succeeded — the broker detects the duplicate via sequence number and
    # discards it. You get exactly one copy, even with retries.
    #
    # Requires: acks="all" and retries > 0 (both set above).
    # Always True in production. There is no good reason to turn it off.
    "enable.idempotence": True,
}


# =============================================================================
# CONSUMER CONFIGURATION FACTORY
# =============================================================================
# Returns a consumer configuration dictionary for a given group ID.
#
# WHY A FUNCTION INSTEAD OF A STATIC DICT?
#   Each consumer group needs a different group.id.
#   Everything else is the same across all consumers.
#   A function lets us generate the right config for each group
#   without duplicating the shared settings three times.
#
# USAGE:
#   from config import consumer_config
#   config = consumer_config("fluxcart-analytics")
#   consumer = Consumer(config)

def consumer_config(group_id: str, offset_reset: str = "earliest") -> dict:
    """
    Generate a Kafka consumer configuration dictionary.

    Args:
        group_id:     Unique identifier for this consumer group.
                      All instances with the same group_id share partition work.
                      Different group_ids read the same topic independently.

        offset_reset: What to do when a consumer group reads a topic
                      for the very first time (no committed offset exists yet).

                      "earliest" = start from the very beginning of the topic.
                                   The consumer reads ALL historical events.
                                   Use for: analytics, audit, replay scenarios.

                      "latest"   = start from the end, only read NEW events.
                                   Events produced before this consumer started
                                   are skipped entirely.
                                   Use for: real-time alerting where historical
                                   data is irrelevant (e.g. live fraud detection).

    Returns:
        dict: Complete consumer configuration ready to pass to Consumer().
    """

    return {

        # bootstrap.servers: same as producer — entry point to the cluster.
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,

        # group.id: THE most important consumer setting.
        # All consumer instances with the same group.id form one consumer group.
        # Kafka divides the topic's partitions among the group's instances.
        # Different group.ids read the same topic completely independently.
        "group.id": group_id,

        # auto.offset.reset: what to do on first read (explained above).
        "auto.offset.reset": offset_reset,

        # -------------------------------------------------------------------------
        # OFFSET COMMIT MODE — manual vs automatic
        # -------------------------------------------------------------------------
        # enable.auto.commit: when True, Kafka automatically commits the offset
        # of the last FETCHED message every 5 seconds — regardless of whether
        # your code actually processed it successfully.
        #
        # THE PROBLEM WITH AUTO COMMIT:
        #   Consumer fetches messages 0-99.
        #   Auto-commit fires, records offset 99 as processed.
        #   Consumer crashes while processing message 50.
        #   On restart, consumer starts at 100 — messages 50-99 are LOST FOREVER.
        #
        # WITH MANUAL COMMIT (enable.auto.commit: False):
        #   Consumer fetches messages 0-99.
        #   Consumer processes all 100 successfully.
        #   Consumer calls commit() — NOW offset 99 is recorded.
        #   If consumer crashes at message 50, restart begins at 0.
        #   Messages 0-49 are reprocessed (at-least-once), nothing is lost.
        #
        # We always use manual commits in production. Always.
        "enable.auto.commit": False,

        # -------------------------------------------------------------------------
        # HEARTBEAT AND SESSION SETTINGS
        # -------------------------------------------------------------------------
        # session.timeout.ms: if Kafka does not hear from a consumer within this
        # time, it declares the consumer dead and triggers a rebalance.
        # 30 seconds gives consumers enough time to process a batch before
        # Kafka thinks they crashed.
        "session.timeout.ms": 30000,

        # heartbeat.interval.ms: how often the consumer sends a heartbeat to
        # Kafka saying "I am still alive". Must be less than session.timeout.ms.
        # 10 seconds = sends heartbeat 3x before session timeout — safe margin.
        "heartbeat.interval.ms": 10000,

        # max.poll.interval.ms: maximum time between two poll() calls.
        # If your processing takes longer than this, Kafka assumes the consumer
        # is stuck and removes it from the group, triggering a rebalance.
        # 5 minutes is generous — adjust down if your processing is fast.
        "max.poll.interval.ms": 300000,
    }


# =============================================================================
# CONSUMER GROUP IDs
# =============================================================================
# Named constants for each consumer group.
# Same principle as topic name constants — use these instead of raw strings.
#
# Each group reads the same topics completely independently.
# Changing one group's ID here does not affect the others.

GROUP_ANALYTICS  = "fluxcart-analytics"    # reads behavior + orders
GROUP_FRAUD      = "fluxcart-fraud"        # reads payments + orders
GROUP_INVENTORY  = "fluxcart-inventory"    # reads orders only


# =============================================================================
# PIPELINE SETTINGS
# =============================================================================
# Shared settings used across producer and consumers.

# How many events the producer generates per second.
# 100 events/sec = 6,000/minute = 360,000/hour.
# Comfortably handled by a 3-broker cluster — good for local demonstration.
EVENTS_PER_SECOND = 100

# How many messages a consumer processes before committing its offset.
# 100 = commit after every 100 messages.
# Lower = safer (less reprocessing on crash) but more Kafka write overhead.
# Higher = faster (fewer commits) but more reprocessing on crash.
CONSUMER_COMMIT_BATCH_SIZE = 100

# How many seconds each consumer waits before emitting a window report.
# 10 seconds = students see a fresh analytics/fraud/inventory report every 10s.
CONSUMER_WINDOW_SECONDS = 10

# after writing this file run : grep "KAFKA_BOOTSTRAP_SERVERS" config.py
# after this you go to setup_topics and run it using python setup_topics.py

# you might get broker 2 error , avoid it

