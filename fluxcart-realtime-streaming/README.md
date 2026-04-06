# FluxCart Kafka to Snowflake to dbt Pipeline
## Comprehensive Documentation | A to Z

**Project Date:** March 17, 2026  
**Technology Stack:** Apache Kafka, Python, Snowflake, dbt, Streamlit, Docker

---

## TABLE OF CONTENTS

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Data Models & Events](#data-models--events)
4. [Kafka Infrastructure Setup](#kafka-infrastructure-setup)
5. [Producer: Event Generation](#producer-event-generation)
6. [Consumers: Real-Time Processing](#consumers-real-time-processing)
7. [Snowflake Integration & Export](#snowflake-integration--export)
8. [dbt Transformation Layer](#dbt-transformation-layer)
9. [Terminal Commands Reference](#terminal-commands-reference)
10. [Complete Pipeline Execution Guide](#complete-pipeline-execution-guide)
11. [Monitoring & Dashboard](#monitoring--dashboard)

---

## ARCHITECTURE OVERVIEW

### End-to-End Data Flow

```
Event Sources (simulated)
        ↓
   Producer.py
   (Generates events)
        ↓
   Kafka Cluster (3 Brokers)
   ├─ Topic: fluxcart.user.behavior (6 partitions)
   ├─ Topic: fluxcart.orders (3 partitions)
   ├─ Topic: fluxcart.payments (3 partitions)
   └─ Topic: fluxcart.fraud.alerts (1 partition)
        ↓
   Three Consumers (Real-Time Processing)
   ├─ AnalyticsConsumer → Aggregates behavior + orders
   ├─ FraudConsumer → Detects suspicious payments
   └─ InventoryConsumer → Tracks stock movement
        ↓
   Snowflake Export (bi_integration/export.py)
   └─ Pushes aggregated data to Snowflake every 60 seconds
        ↓
   Snowflake Data Warehouse
   ├─ RAW schema (raw Kafka data)
   ├─ STAGING layer (transformed)
   └─ MART layer (business-ready)
        ↓
   dbt (Transform & Build Models)
   ├─ Staging models (stg_analytics, stg_fraud, stg_inventory)
   └─ Mart models (mart_business_health)
        ↓
   Analytics & Visualization
   ├─ Streamlit Dashboard
   ├─ dbt Docs
   └─ BI Tools
```

### Why This Architecture?

- **Kafka**: High-volume real-time event streaming (50-100 events/second)
- **Python Consumers**: Business logic for fraud detection, analytics, inventory
- **Snowflake**: Scalable cloud data warehouse for historical analysis
- **dbt**: Version-controlled SQL transformations and data quality tests
- **Streamlit**: Live dashboard for monitoring KPIs

---

## SYSTEM COMPONENTS

### 1. **Kafka Cluster** (Docker-based)
- **3 Brokers** in KRaft mode (no ZooKeeper)
- **5 Topics** with different retention policies
- **Partition Strategy**: High-volume topics (behavior) = 6 partitions; low-volume (fraud) = 1 partition
- **Replication Factor**: 3 (survives 1 broker failure)

### 2. **Python Producer** (`producer.py`)
- Generates realistic e-commerce events
- 50-100 events/second configurable rate
- Event mix: 65% user behavior, 25% orders, 10% payments
- Tracks delivery metrics by topic and partition

### 3. **Python Consumers** (3 independent processes)
- **AnalyticsConsumer**: Reads behavior + orders → aggregates KPIs
- **FraudConsumer**: Reads payments + orders → detects fraud patterns
- **InventoryConsumer**: Reads orders → tracks stock & warehouse activity
- Each runs its own consumer group for independent processing

### 4. **Batch Exporter** (`bi_integration/export.py`)
- Runs 3 exporters in parallel (analytics, fraud, inventory)
- Batches events into DataFrames
- Pushes to Snowflake every 60 seconds
- Stores backups as CSV files

### 5. **Snowflake Data Warehouse**
- **Account**: SVHBWDV-PS62195
- **Database**: KAFKA_DB
- **Warehouse**: KAFKA_WH
- **Main Schema**: RAW (auto-created tables from Kafka export)

### 6. **dbt Project** (`./shopstream/`)
- **Version**: 1.0.0
- **Profile**: shopstream (configured in dbt_project.yml)
- **Model Layers**: Staging → Mart
- **Materialization**: Views (staging), Tables (marts)

### 7. **Streamlit Dashboard** (`streamlit_pipeline.py`)
- Auto-refreshing every 30 seconds
- Real-time KPI metrics
- Interactive charts (Plotly-based)
- Fraud alerts with severity levels

---

## DATA MODELS & EVENTS

### Event 1: UserBehaviorEvent

**Produced by**: `producer.py`  
**Consumed by**: `AnalyticsConsumer`, `AnalyticsExporter`  
**Topic**: `fluxcart.user.behavior` (6 partitions)  
**Partition Key**: `user_id` (ensures all user events go to same partition)  
**Retention**: 30 days

**Fields**:
```python
event_id: str              # unique event identifier (UUID)
user_id: str              # "user-0001" to "user-0050"
timestamp: str            # ISO 8601 format
action: str              # "view", "search", "add_to_cart", "remove_from_cart", "wishlist"
product_id: str          # "elec-001", "clth-003", etc.
category: str            # "electronics", "clothing", "books", "home", "sports"
price: float             # product price in INR
device: str              # "web", "mobile-ios", "mobile-android", "tablet", "smart-tv"
country: str             # "IN", "US", "GB", "DE", "SG", "AE", "AU", "CA"
session_duration_secs: int  # seconds spent browsing
```

### Event 2: OrderEvent

**Produced by**: `producer.py`  
**Consumed by**: `AnalyticsConsumer`, `FraudConsumer`, `InventoryConsumer`, Exporters  
**Topic**: `fluxcart.orders` (3 partitions)  
**Partition Key**: `order_id`  
**Retention**: 90 days

**Fields**:
```python
order_id: str               # unique order identifier
user_id: str               # customer placing order
product_id: str            # what they ordered
quantity: int              # how many units
order_total: float         # total price in INR
currency: str              # "INR"
order_status: str          # "placed", "confirmed", "packed", "shipped", "delivered", "cancelled"
warehouse_id: str          # "wh-mumbai", "wh-delhi", etc.
created_at: str            # when order was created
updated_at: str            # last status change
```

### Event 3: PaymentEvent

**Produced by**: `producer.py`  
**Consumed by**: `FraudConsumer`, `FraudExporter`  
**Topic**: `fluxcart.payments` (3 partitions)  
**Partition Key**: `order_id`  
**Retention**: 90 days

**Fields**:
```python
payment_id: str            # unique payment identifier
order_id: str              # which order this pays for
user_id: str               # who's paying
amount: float              # payment amount in INR
currency: str              # "INR"
payment_method: str        # "credit_card", "debit_card", "upi", "netbanking", "wallet"
payment_status: str        # "initiated", "success", "failed", "refunded"
timestamp: str             # when payment was processed
account_age_days: int      # how old is the user account (0-365 days)
account_created_at: str    # account creation date
```

### Event 4: FraudAlert (produced by FraudConsumer)

**Produced by**: `FraudConsumer` when fraud rules trigger  
**Consumed by**: `FraudExporter`  
**Topic**: `fluxcart.fraud.alerts` (1 partition)  
**Retention**: 30 days

**Fields**:
```python
alert_id: str              # unique alert identifier
user_id: str               # the suspicious user
order_id: str              # the suspicious order
payment_id: str            # the suspicious payment
risk_level: str            # "HIGH", "MEDIUM", "LOW"
rule_triggered: str        # "new_account_large_payment", "large_payment", "failed_payment"
amount: float              # payment amount that triggered alert
reason: str                # human-readable explanation
detected_at: str           # when fraud detection fired
```

---

## KAFKA INFRASTRUCTURE SETUP

### Docker Compose Configuration

**File**: `docker-compose.yml`

**What it creates**:
- 3 Kafka brokers in KRaft mode (unified metadata)
- Named Docker network: `fluxcart-network`
- Persistent volumes for data durability

**Broker Configuration**:

| Broker | Role | Port | Internal Address |
|--------|------|------|------------------|
| broker-1 | Controller + Broker | 9092 | broker-1:29092 |
| broker-2 | Broker Only | 9093 | broker-2:29093 |
| broker-3 | Broker Only | 9094 | broker-3:29094 |

**Key Environment Variables**:
```bash
KAFKA_NODE_ID=1                              # Unique ID per broker
KAFKA_PROCESS_ROLES=broker,controller        # Roles this broker plays
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=3     # Replicate offset data across all brokers
KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=3
KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=2        # Min 2 replicas needed for writes
KAFKA_LISTENERS=PLAINTEXT://broker-1:29092   # Internal listener (Docker network)
KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092  # External listener (producer/consumer)
```

### Topic Creation Configuration

**File**: `config.py` → `TOPIC_CONFIGS` dict

```python
TOPIC_USER_BEHAVIOR = {
    "num_partitions": 6,           # High volume → more parallelism
    "replication_factor": 3,       # Survives 1 broker failure
    "retention_ms": 2592000000,    # 30 days
}

TOPIC_ORDERS = {
    "num_partitions": 3,           # Medium volume
    "replication_factor": 3,
    "retention_ms": 7776000000,    # 90 days (business/compliance requirement)
}

TOPIC_PAYMENTS = {
    "num_partitions": 3,           # Medium volume
    "replication_factor": 3,
    "retention_ms": 7776000000,    # 90 days (financial records)
}

TOPIC_FRAUD_ALERTS = {
    "num_partitions": 1,           # Low volume, single consumer reads all
    "replication_factor": 3,
    "retention_ms": 2592000000,    # 30 days
}

TOPIC_DEAD_LETTER = {
    "num_partitions": 1,           # Unprocessable messages land here
    "replication_factor": 3,
    "retention_ms": 2592000000,    # 30 days
}
```

### Partition Strategy Rationale

**Why 6 partitions for user.behavior?**
- ~3500 behavior events/minute (65% of 50-100 events/sec)
- 6 partitions allow up to 6 analytics consumers running in parallel
- Each consumer reads 1 partition (no co-partition contention)

**Why 1 partition for fraud.alerts?**
- Low volume (typically 5-15 alerts/minute)
- Single FraudExporter reads all fraud → no need for parallelism
- Easier to guarantee total ordering of alerts

---

## PRODUCER: EVENT GENERATION

### File: `producer.py`

### Purpose
Simulates the entire FluxCart platform by generating realistic events at a configurable rate.

### Event Generation Mix
```
65% UserBehaviorEvent  → fluxcart.user.behavior
25% OrderEvent         → fluxcart.orders
10% PaymentEvent       → fluxcart.payments
```

### Key Classes and Functions

#### ProducerMetrics Class
Tracks delivery statistics in real-time:

```python
class ProducerMetrics:
    total_sent: int              # successful deliveries
    total_failed: int            # failed deliveries
    by_topic: dict               # counts per topic
    by_partition: dict           # counts per partition (e.g., "topic-P0": 150)
    start_time: float            # when producer started
```

**Methods**:
- `record_success(topic, partition)` — increment counters when message delivered
- `record_failure(topic)` — increment error counter
- `report()` — print human-readable metrics every 10 seconds

#### FluxCartProducer Class
Main producer class:

```python
class FluxCartProducer:
    EVENTS_PER_SECOND: int = 50              # configurable rate
    REPORT_INTERVAL_SECS: int = 10           # print metrics every 10 seconds
    
    def run(duration_seconds: int)           # run for N seconds
    def _generate_event() -> (str, str, bytes)  # topic, key, serialized_event
    def _delivery_callback(err, msg)         # called when Kafka confirms delivery
```

### How Events Are Generated

**1. Random Event Type Selection**:
```python
rand = random.random()
if rand < 0.65:      event = UserBehaviorEvent.generate()
elif rand < 0.90:    event = OrderEvent.generate()
else:                event = PaymentEvent.generate()
```

**2. Partition Key Strategy**:
```
UserBehaviorEvent   → partition_key = user_id
                       (all events for user-0023 go to same partition)

OrderEvent          → partition_key = order_id
                       (all status updates for order go to same partition)

PaymentEvent        → partition_key = order_id
                       (payment updates stay with order lifecycle)
```

**3. Serialization**:
Each event is converted to JSON and encoded as UTF-8 bytes before publishing:
```python
message_bytes = json.dumps(event.to_dict()).encode('utf-8')
producer.produce(topic=topic, key=key, value=message_bytes)
```

### Delivery Guarantees

**Producer Configuration** (from `config.py` → `PRODUCER_CONFIG`):
```python
{
    "bootstrap.servers": "localhost:9092,localhost:9093,localhost:9094",
    "acks": "all",           # Wait for all replicas to acknowledge (most durable)
    "retries": 3,            # Retry 3 times if broker is unavailable
    "max.in.flight.requests.per.connection": 5,  # Pipeline 5 requests
    "batch.size": 16384,     # Batch 16KB or 100ms, whichever comes first
    "linger.ms": 100,        # Wait up to 100ms to fill batch
    "compression.type": "snappy",  # Compress batches with Snappy
}
```

**acks="all" Explanation**:
- Producer waits for leader broker AND all in-sync replicas (ISRs) to confirm
- If leader is broker-1, waits for broker-2 AND broker-3 to also write message
- Ensures message survives 1 broker failure
- Trade-off: slightly higher latency, but zero data loss

### Running the Producer

**Basic**:
```bash
python3 producer.py
```

**With Duration (default 120 seconds)**:
```bash
# Runs for 120 seconds, generating 50 events/second
python3 producer.py
```

**Sample Output**:
```
[producer] Initializing Kafka producer...
[producer] Connected. Generating events for 120 seconds at 50 events/sec

[METRICS] Rate: 50.2 evt/sec | Sent: 502 | Failed: 0
[METRICS] By topic: behavior=326 | orders=126 | payments=50
[METRICS] Top partitions: behavior-P0=58, behavior-P2=56, behavior-P4=54

[METRICS] Rate: 49.8 evt/sec | Sent: 1004 | Failed: 0

...after 120 seconds...

[FINAL] Total sent: 6000 | Failed: 0 | Duration: 120.5s | Avg rate: 49.8 evt/s
```

---

## CONSUMERS: REAL-TIME PROCESSING

### Architecture: Base Consumer Pattern

All three consumers inherit from `BaseConsumer` (in `consumers/base_consumer.py`), which provides:

- Kafka Consumer initialization and configuration
- Poll loop (continuous event reading)
- Manual offset commit strategy (batch commits every 100 messages)
- Dead letter routing (unprocessable events sent to `fluxcart.dead.letter`)
- Window-based reporting (print summary every 10 seconds)
- Graceful shutdown (Ctrl+C cleanup)

Each consumer implements 3 methods:
1. `topics()` → returns list of topics to subscribe to
2. `process(event, topic)` → business logic for processing event
3. `emit_report()` → print 10-second window summary

### Consumer 1: AnalyticsConsumer

**File**: `consumers/analytics.py`  
**Group ID**: `fluxcart-analytics`  
**Topics**: `fluxcart.user.behavior`, `fluxcart.orders`

**Purpose**: Aggregates user behavior and order data into KPIs

**Window State** (resets every 10 seconds):
```python
behavior_count: int             # total behavior events seen
action_counts: dict             # {"view": 450, "add_to_cart": 120, ...}
product_counts: dict            # {"elec-001": 22, "home-004": 18, ...}
category_counts: dict           # {"electronics": 85, "clothing": 42, ...}
device_counts: dict             # {"web": 200, "mobile-ios": 150, ...}
country_counts: dict            # {"IN": 250, "US": 100, ...}

order_count: int                # total orders in window
order_status_counts: dict       # {"placed": 45, "confirmed": 30, ...}
order_totals: list              # [2500, 3400, 1200, ...]  (for sum/avg)
```

**Business Logic**:

**For UserBehaviorEvent**:
- Increment appropriate counters (action, product, category, device, country)
- Track session duration
- No complex calculations (just counting)

**For OrderEvent**:
- Track order status distribution
- Accumulate order totals for revenue calculation
- Monitor order flow through lifecycle

**Window Output** (every 10 seconds):
```
[fluxcart-analytics] ════════════════ ANALYTICS WINDOW (10s) ═════════════════
[fluxcart-analytics] Behavior Events: 450
[fluxcart-analytics]   Actions: view=280, add_to_cart=120, search=50
[fluxcart-analytics]   Top Products: elec-001=22, home-004=18, clth-002=15
[fluxcart-analytics]   Top Categories: electronics=85, home=42, clothing=40
[fluxcart-analytics]   Devices: web=250, mobile-ios=120, mobile-android=80
[fluxcart-analytics] Order Events: 113
[fluxcart-analytics]   Status: placed=45, confirmed=30, shipped=18, delivered=10
[fluxcart-analytics]   Revenue (10s window): Rs. 382,450
[fluxcart-analytics] ═══════════════════════════════════════════════════════════
```

### Consumer 2: FraudConsumer

**File**: `consumers/fraud.py`  
**Group ID**: `fluxcart-fraud`  
**Topics**: `fluxcart.payments`, `fluxcart.orders`  
**Produces**: `fluxcart.fraud.alerts`

**Purpose**: Detects suspicious payment patterns and raises fraud alerts in real-time

**Fraud Detection Rules** (applied to every PaymentEvent):

```
RULE 1 — New Account Large Payment
  IF payment_amount > Rs. 50,000 AND account_age < 7 days
  THEN risk_level = "HIGH"
  
  Rationale: Stolen card tested immediately on high-value item

RULE 2 — Unusually Large Payment
  IF payment_amount > Rs. 200,000
  THEN risk_level = "MEDIUM"
  
  Rationale: Any payment above Rs. 2 lakh should be reviewed

RULE 3 — Failed Payment
  IF payment_status == "failed"
  THEN risk_level = "LOW"
  
  Rationale: Single failure is normal, but aggregating failures = card testing
```

**Window State** (resets every 10 seconds):
```python
payment_count: int              # total payments processed
payment_status_counts: dict     # {"success": 32, "initiated": 17, "failed": 7}
failed_payment_count: int       # counter for Rule 3
alerts_raised: list             # [{"alert_id": "...", "rule": "...", ...}, ...]

order_count: int                # orders seen in window
cancelled_order_count: int      # cancelled orders (for trend analysis)
```

**Window Output**:
```
[fluxcart-fraud] ════════════════════ FRAUD WINDOW (10s) ═════════════════════
[fluxcart-fraud] Payments processed: 58
[fluxcart-fraud] By status: success=32, initiated=17, failed=7, refunded=2
[fluxcart-fraud] 
[fluxcart-fraud] ──── Fraud Alerts ────────────────────────────────────────────
[fluxcart-fraud] Alerts raised: 3
[fluxcart-fraud] HIGH  new_account_large_payment  user=user-0023  Rs.87,400
[fluxcart-fraud] MEDIUM large_payment             user=user-0041  Rs.245,000
[fluxcart-fraud] LOW   failed_payment             user=user-0017  Rs.12,400
[fluxcart-fraud]
[fluxcart-fraud] ──── Orders ──────────────────────────────────────────────────
[fluxcart-fraud] Order events: 113
[fluxcart-fraud] Cancelled orders: 4
[fluxcart-fraud] ════════════════════════════════════════════════════════════════
```

### Consumer 3: InventoryConsumer

**File**: `consumers/inventory.py`  
**Group ID**: `fluxcart-inventory`  
**Topics**: `fluxcart.orders`  
**Produces**: Nothing (pure read-only consumer)

**Purpose**: Tracks inventory movement, warehouse activity, and stock distribution

**Window State** (resets every 10 seconds):
```python
order_count: int                # total orders in window
order_status_counts: dict       # {"placed": 58, "confirmed": 30, ...}

units_ordered: int              # sum of quantities in "placed" orders
units_delivered: int            # sum of quantities in "delivered" orders
units_cancelled: int            # sum of quantities in "cancelled" orders

product_counts: dict            # {"elec-003": 12, "home-004": 11, ...}
category_counts: dict           # {"electronics": 41, "home": 38, ...}
warehouse_counts: dict          # {"wh-mumbai": 38, "wh-delhi": 31, ...}
```

**Window Output**:
```
[fluxcart-inventory] ═════════════ INVENTORY WINDOW (10s) ════════════════════
[fluxcart-inventory] Orders received: 141
[fluxcart-inventory]
[fluxcart-inventory] ──── By Status ────────────────────────────────────────────
[fluxcart-inventory] placed=58, confirmed=30, shipped=19, delivered=17, cancelled=13, packed=4
[fluxcart-inventory]
[fluxcart-inventory] ──── Stock Movement ───────────────────────────────────────
[fluxcart-inventory] Units ordered: 187
[fluxcart-inventory] Units delivered: 22
[fluxcart-inventory] Units cancelled: 16
[fluxcart-inventory]
[fluxcart-inventory] ──── Top Products ────────────────────────────────────────
[fluxcart-inventory] elec-003=12, home-004=11, clth-001=9, book-002=8, sprt-005=7
[fluxcart-inventory]
[fluxcart-inventory] ──── Top Categories ──────────────────────────────────────
[fluxcart-inventory] electronics=41, home=38, clothing=32, books=25, sports=20
[fluxcart-inventory]
[fluxcart-inventory] ──── Warehouse Activity ───────────────────────────────────
[fluxcart-inventory] wh-mumbai=38, wh-delhi=31, wh-bangalore=28, wh-hyderabad=26, wh-chennai=18
[fluxcart-inventory] ════════════════════════════════════════════════════════════
```

### Consumer Configuration (config.py)

```python
def consumer_config(group_id: str) -> dict:
    """
    Builds a Kafka consumer configuration dictionary.
    Each consumer passes its own group_id.
    """
    return {
        "bootstrap.servers": "localhost:9092,localhost:9093,localhost:9094",
        "group.id": group_id,       # e.g., "fluxcart-analytics"
        "auto.offset.reset": "earliest",  # Start from beginning if no committed offset
        "enable.auto.commit": False,      # Manual commits (see batch_commit logic)
        "max.poll.interval.ms": 300000,   # 5 minutes (time between poll() calls)
        "session.timeout.ms": 6000,       # 6 seconds (heartbeat interval)
    }
```

**Key Consumer Settings Explained**:

| Setting | Value | Why |
|---------|-------|-----|
| `auto.offset.reset` | `earliest` | If consumer crashes, restart from oldest message, not fail |
| `enable.auto.commit` | `False` | Manual commits ensure we don't lose track of progress if consumer dies |
| `max.poll.interval.ms` | 300000ms | Consumer has 5 minutes between poll() calls before Kafka considers it dead |
| `session.timeout.ms` | 6000ms | Heartbeat sent every 6 seconds to broker to stay alive |

### Offset Commit Strategy

**Why Manual Commits?**
- Auto-commit can lose messages if consumer crashes after processing but before commit
- Manual control lets us commit only after successful processing

**Batch Commit Implementation**:
```python
CONSUMER_COMMIT_BATCH_SIZE = 100  # Commit every 100 messages

# In consumer loop:
for event in events:
    process(event)
    batch_count += 1
    if batch_count >= 100:
        consumer.commit()  # Write offset to Kafka
        batch_count = 0
```

**Trade-off**:
- Committing every 1 message = 6000 network round-trips/minute (overhead)
- Committing every 100 messages = 60 network round-trips/minute (efficient)
- Cost: if consumer crashes after processing 99 messages, restart will re-process them

---

## SNOWFLAKE INTEGRATION & EXPORT

### File: `bi_integration/export.py`

### Architecture: Three Parallel Exporters

```
Analytics Data Thread       Fraud Data Thread       Inventory Data Thread
      ↓                           ↓                           ↓
Subscribe to:              Subscribe to:           Subscribe to:
- user.behavior            - payments              - orders
- orders                   - orders

Aggregate into:             Aggregate into:         Aggregate into:
- behavior_events          - fraud_alerts          - order_status_counts
- order_events             - failed_payments       - units_ordered/delivered
- revenue_totals                                   - product_counts

Every 60 seconds:           Every 60 seconds:       Every 60 seconds:
batch → DataFrame          batch → DataFrame       batch → DataFrame
      ↓                           ↓                           ↓
    Push to                    Push to                    Push to
    Snowflake                  Snowflake                  Snowflake
    ANALYTICS_SUMMARY          FRAUD_ALERTS               INVENTORY_SUMMARY
```

### Snowflake Configuration

```python
SNOW_CONFIG = {
    "user": "KAFKA_USER",
    "password": "KAFKAPassword2602",
    "account": "SVHBWDV-PS62195",  # org-account format
    "warehouse": "KAFKA_WH",        # compute cluster for queries
    "database": "KAFKA_DB",         # logical database container
    "schema": "RAW",                # raw event data lands here
    "role": "KAFKA_ROLE"            # database role with permissions
}

EXPORT_INTERVAL_SECONDS = 60  # Batch and export every 60 seconds
```

### Data Flow: AnalyticsExporter

**Kafka Topics Subscribed**:
- `fluxcart.user.behavior`
- `fluxcart.orders`

**Window Aggregation** (every 10 seconds):
```python
behavior_count: int              # count of behavior events
action_counts: dict              # {"view": 162, "add_to_cart": 400, ...}
product_counts: dict             # top 20 products
category_counts: dict            # {"electronics": 1200, ...}
order_count: int                 # count of orders
order_totals: list               # [2500, 3400, 1200, ...] for sum/avg
```

**Export Function** (every 60 seconds):
```python
def _flush_window():
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "behavior_events": self.behavior_count,
        "order_events": self.order_count,
        "total_revenue": round(sum(self.order_totals), 2)
    }
    analytics_rows.append(row)
    # When 60 seconds elapse, analytics_rows [] → DataFrame → Snowflake
```

**Snowflake Table** (`ANALYTICS_SUMMARY`):
```sql
TIMESTAMP         BEHAVIOR_EVENTS  ORDER_EVENTS  TOTAL_REVENUE
─────────────────────────────────────────────────────────────
2026-03-17T10:00:23Z    450            113          382450.00
2026-03-17T10:01:23Z    480            118          405320.50
2026-03-17T10:02:23Z    445            105          367890.25
```

### Data Flow: FraudExporter

**Kafka Topics Subscribed**:
- `fluxcart.fraud.alerts` (written by FraudConsumer)

**Window Aggregation** (every 60 seconds):
```python
fraud_rows: list  # Each row is one fraud alert
# {
#   "timestamp": "...",
#   "user_id": "user-0023",
#   "alert_id": "alert-xxxxx",
#   "risk_level": "HIGH",
#   "rule_triggered": "new_account_large_payment",
#   "amount": 87400.00
# }
```

**Snowflake Table** (`FRAUD_ALERTS`):
```sql
TIMESTAMP              ALERT_ID    USER_ID      RISK_LEVEL  RULE_TRIGGERED              AMOUNT
────────────────────────────────────────────────────────────────────────────────────────────────
2026-03-17T10:00:45Z  alert-001  user-0023    HIGH        new_account_large_payment   87400.00
2026-03-17T10:01:12Z  alert-002  user-0041    MEDIUM      large_payment               245000.00
2026-03-17T10:01:58Z  alert-003  user-0017    LOW         failed_payment              12400.00
```

### Data Flow: InventoryExporter

**Kafka Topics Subscribed**:
- `fluxcart.orders`

**Window Aggregation** (every 60 seconds):
```python
inventory_rows: list  # Contains aggregated inventory metrics
# {
#   "timestamp": "...",
#   "units_ordered": 187,
#   "units_delivered": 22,
#   "units_cancelled": 16,
#   "top_product": "elec-003",
#   "warehouse_activity": {"wh-mumbai": 38, "wh-delhi": 31, ...}
# }
```

**Snowflake Table** (`INVENTORY_SUMMARY`):
```sql
TIMESTAMP              UNITS_ORDERED  UNITS_DELIVERED  UNITS_CANCELLED  TOP_PRODUCT
──────────────────────────────────────────────────────────────────────────────────
2026-03-17T10:00:23Z       187               22              16           elec-003
2026-03-17T10:01:23Z       192               25              14           home-004
2026-03-17T10:02:23Z       178               19              18           clth-001
```

### Snowflake Write Process

```python
def push_to_snowflake(data_list, table_name):
    """
    3-step process to push data to Snowflake:
    
    1. Connect to Snowflake using the SNOW_CONFIG credentials
    2. Convert Python list of dicts → pandas DataFrame
    3. Use write_pandas (high-speed bulk insert) to push data
    """
    
    if not data_list:
        print(f"No new data to upload for {table_name}")
        return
    
    try:
        # Step 1: Establish connection
        conn = snowflake.connector.connect(**SNOW_CONFIG)
        
        # Step 2: Convert to DataFrame
        df = pd.DataFrame(data_list)
        
        # Step 3: Standardize column names (Snowflake expects UPPERCASE)
        df.columns = [c.upper() for c in df.columns]
        
        # Step 4: High-speed bulk insert
        success, nchunks, nrows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=table_name.upper(),
            auto_create_table=True  # Auto-create if doesn't exist
        )
        
        if success:
            print(f"❄️  Pushed {nrows} rows to {table_name}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Snowflake Error: {e}")
```

### CSV Backup (Local Storage)

Exporter also writes CSV backups for local testing:

```python
# At the end of export cycle
analytics_df.to_csv("bi_integration/data/analytics_summary.csv", index=False)
fraud_df.to_csv("bi_integration/data/fraud_alerts.csv", index=False)
inventory_df.to_csv("bi_integration/data/inventory_summary.csv", index=False)
```

These CSV files feed the Streamlit dashboard.

---

## DBT TRANSFORMATION LAYER

### Project Structure

```
shopstream/
├── dbt_project.yml                # Main dbt config
├── models/
│   └── example/
│       ├── Staging/               # Layer 1: minimal transformation
│       │   ├── stg_analytics.sql
│       │   ├── stg_fraud.sql
│       │   └── stg_inventory.sql
│       │
│       └── Mart/                  # Layer 2: business-ready tables
│           └── mart_business_health.sql
│
├── target/                        # Generated artifacts (don't edit)
│   ├── compiled/                  # SQL after Jinja templating
│   ├── run/                       # Execution results
│   ├── manifest.json              # Dependency graph
│   └── run_results.json           # Test results
│
└── README.md
```

### dbt_project.yml Configuration

```yaml
name: 'shopstream'
version: '1.0.0'
profile: 'shopstream'         # Read profiles.yml for "shopstream" config

model-paths: ["models"]       # Where dbt looks for SQL models
analysis-paths: ["analyses"]  # Where ad-hoc SQL lives
test-paths: ["tests"]         # Where data quality tests live
seed-paths: ["seeds"]         # CSV files to load as tables
macro-paths: ["macros"]       # Jinja macros and functions

models:
  shopstream:
    example:
      +materialized: view     # Default: all models are views (recommended for staging)
```

### Staging Layer Models

**Purpose**: Minimal transformation, slight cleaning, column naming

#### stg_analytics.sql

**Input**: Snowflake `ANALYTICS_SUMMARY` table  
**Materialization**: View (lightweight transformation)  
**Output**: `stg_analytics` (virtual table)

```sql
{{ config(materialized='view') }}

select
    "TIMESTAMP"::timestamp as event_at,
    "BEHAVIOR_EVENTS"::int as behavior_count,
    "ORDER_EVENTS"::int as order_count,
    "TOTAL_REVENUE"::float as total_revenue
from {{ source('kafka_source', 'ANALYTICS_SUMMARY') }}
```

**Why this model**:
- Source is from Kafka raw export → column names are UPPERCASE, types are strings
- This view casts to proper types and gives friendly names
- Downstream models use `event_at`, `behavior_count`, not `"TIMESTAMP"`

**dbt Functions Used**:
- `{{ config(materialized='view') }}` — This is a view, not a physical table
- `{{ source('kafka_source', 'ANALYTICS_SUMMARY') }}` — References Snowflake source

#### stg_fraud.sql

**Input**: Snowflake `FRAUD_ALERTS` table  
**Materialization**: View

```sql
{{ config(materialized='view') }}

select
    "TIMESTAMP"::timestamp as alert_timestamp,
    "ALERT_ID"::string as alert_id,
    "USER_ID"::string as user_id,
    "RISK_LEVEL"::string as risk_level,
    "RULE_TRIGGERED"::string as rule_triggered,
    "AMOUNT"::float as alert_amount
from {{ source('kafka_source', 'FRAUD_ALERTS') }}
```

#### stg_inventory.sql

**Input**: Snowflake `INVENTORY_SUMMARY` table  
**Materialization**: View

```sql
{{ config(materialized='view') }}

select
    "TIMESTAMP"::timestamp as event_timestamp,
    "UNITS_ORDERED"::int as units_ordered,
    "UNITS_DELIVERED"::int as units_delivered,
    "UNITS_CANCELLED"::int as units_cancelled,
    "TOP_PRODUCT"::string as top_product
from {{ source('kafka_source', 'INVENTORY_SUMMARY') }}
```

### Mart Layer Models

**Purpose**: Business-ready KPIs and metrics for analysis

#### mart_business_health.sql

**Input**: `fct_daily_summary` (a fact table built from staging models)  
**Materialization**: Table (persisted for fast queries)  
**Output**: `mart_business_health` — final analytics table

```sql
{{ config(materialized='table') }}

with daily_data as (
    select * from {{ ref('fct_daily_summary') }}
)

select
    event_date,
    gross_revenue,
    potential_fraud_loss,
    (gross_revenue - potential_fraud_loss) as net_revenue,
    alert_count,
    current_stock,
    -- KPI: Is our stock keeping up with traffic?
    round(current_stock / nullif(behaviors, 0), 2) as stock_to_behavior_ratio
from daily_data
```

**Business Logic**:

| Column | Formula | Business Value |
|--------|---------|-----------------|
| `net_revenue` | gross_revenue - fraud_loss | Actual profit after fraud adjustment |
| `stock_to_behavior_ratio` | stock / behaviors | Inventory efficiency: units per customer action |
| `alert_count` | COUNT(fraud_alerts) | Risk monitoring metric |

**dbt Functions Used**:
- `{{ config(materialized='table') }}` — Materialized as physical table (faster queries than view)
- `{{ ref('fct_daily_summary') }}` — References another model by name (dbt handles dependencies)
- `nullif(behaviors, 0)` — Avoid division by zero

### How dbt Works

```bash
# Step 1: Parse
dbt parses all .sql files, builds dependency graph
(stg_analytics → mart depends on fct_daily_summary)

# Step 2: Compile
dbt processes Jinja templating:
    {{ ref('...') }} → resolved to schema.table_name
    {{ config(...) }} → applied to generate CREATE VIEW/TABLE
    {{ source(...) }} → resolved to raw Snowflake schema

# Step 3: Execute
dbt runs compiled SQL in Snowflake in dependency order:
    1. Create view: stg_analytics
    2. Create view: stg_fraud
    3. Create view: stg_inventory
    4. Create table: fct_daily_summary (if exists)
    5. Create table: mart_business_health

# Step 4: Test & Docs
dbt runs tests (if defined), generates docs/graph
```

### dbt Profile Configuration (profiles.yml)

Typically in `~/.dbt/profiles.yml`:

```yaml
shopstream:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: SVHBWDV-PS62195
      user: KAFKA_USER
      password: KAFKAPassword2602
      database: KAFKA_DB
      schema: DBT_DEV
      warehouse: KAFKA_WH
      threads: 4
      client_session_keep_alive: true
```

---

## TERMINAL COMMANDS REFERENCE

### 1. Docker & Kafka Setup

**Start Kafka cluster**:
```bash
docker compose up -d
```
Creates 3 brokers in background, volumes persist data.

**Stop Kafka cluster**:
```bash
docker compose down
```
Stops containers, data persists on disk.

**Stop Kafka and delete all data**:
```bash
docker compose down -v
```
Removes containers AND volumes (fresh start).

**Check Kafka logs**:
```bash
docker compose logs -f broker-1
```
Follow logs from broker-1 in real-time (Ctrl+C to stop).

**Check all broker status**:
```bash
docker compose ps
```
Shows all 3 brokers (running/stopped).

---

### 2. Kafka Topic Setup

**Create topics** (one-time only):
```bash
python3 setup_topics.py
```
Creates all 5 topics with correct partitions and retention.

**Check topics exist** (optional):
```bash
docker compose exec broker-1 kafka-topics --bootstrap-server localhost:9092 --list
```
Lists all topics on the cluster.

---

### 3. Producer

**Run producer** (default 120 seconds):
```bash
python3 producer.py
```
Generates 50 events/second in 65/25/10 mix.

**Run producer for custom duration**:
```bash
# Run for 300 seconds
python3 producer.py --duration 300
```

**Output**: Metrics every 10 seconds, final summary at end.

---

### 4. Individual Consumers

**Run analytics consumer**:
```bash
python3 consumers/analytics.py
```
Reads behavior + orders, prints KPI summary every 10 seconds.

**Run fraud consumer**:
```bash
python3 consumers/fraud.py
```
Reads payments + orders, prints fraud alerts every 10 seconds.

**Run inventory consumer**:
```bash
python3 consumers/inventory.py
```
Reads orders, prints stock movement every 10 seconds.

---

### 5. Integrated Pipeline

**Run entire pipeline in one terminal**:
```bash
python3 run_pipeline.py
```
Starts producer + 3 consumers in threads. Press Ctrl+C to stop all gracefully.

**Run pipeline for 5 minutes**:
```bash
python3 run_pipeline.py --duration 300
```

---

### 6. Snowflake Export

**Run exporters** (in separate terminal):
```bash
python3 bi_integration/export.py
```
Starts 3 exporters in parallel threads:
- AnalyticsExporter (user.behavior + orders → ANALYTICS_SUMMARY)
- FraudExporter (fraud.alerts → FRAUD_ALERTS)
- InventoryExporter (orders → INVENTORY_SUMMARY)

Every 60 seconds, batches data and pushes to Snowflake.

---

### 7. dbt Commands

**Navigate to dbt project**:
```bash
cd shopstream
```

**Test Snowflake connection**:
```bash
dbt debug
```
Validates credentials and connectivity.

**Run all models** (compile + execute):
```bash
dbt run
```
Creates staging views + mart tables in `DBT_DEV` schema.

**Run specific model**:
```bash
dbt run --select stg_analytics
```
Only runs that one model.

**Rebuild from scratch** (warning: deletes all models):
```bash
dbt run --full-refresh
```

**Run tests** (if defined):
```bash
dbt test
```
Checks for NULL values, foreign key relationships, etc.

**Generate documentation site**:
```bash
dbt docs generate
```
Creates `target/index.html` and dependency graph.

**Serve documentation** (opens browser):
```bash
dbt docs serve
```
Launches local web server at http://localhost:8000  
Shows data lineage, model descriptions, column types.

Press Ctrl+C to stop server.

---

### 8. Streamlit Dashboard

**Start dashboard**:
```bash
streamlit run streamlit_pipeline.py
```
Launches at http://localhost:8501

**Dashboard Features**:
- Auto-refreshes every 30 seconds
- KPI cards (total revenue, fraud alerts, fulfillment rate)
- Interactive charts (Plotly)
- Fraud alerts table with color-coded risk levels

Press Ctrl+C to stop.

---

## COMPLETE PIPELINE EXECUTION GUIDE

### Prerequisites

**Environment Setup**:
```bash
# Navigate to project root
cd d:\Ironhack\skillset\kafka\Kafka_foundational\Kafka_foundational\fluxcart-pipeline

# Activate Python virtual environment
.\kafkaenv\Scripts\Activate.ps1

# Verify Python and pip
python --version
pip --version
```

**Required Python Packages** (should already be installed):
```bash
pip install confluent-kafka snowflake-connector-python pandas plotly streamlit
```

---

### Execution Steps (Order Matters)

#### **Phase 1: Infrastructure Setup** (1-2 minutes)

**Terminal 1 — Start Kafka Cluster**:
```bash
docker compose up -d
# Output:
# ✓ broker-1
# ✓ broker-2
# ✓ broker-3

# Wait 30 seconds for cluster to stabilize
timeout /t 30
```

**Verify cluster started**:
```bash
docker compose ps
# Should show all 3 brokers: "Up X seconds"
```

---

#### **Phase 2: Topic Creation** (30 seconds)

**Terminal 1 — Create Topics**:
```bash
python3 setup_topics.py
# Output:
# Connecting to Kafka at localhost:9092...
# Connected.
# 
# Creating: fluxcart.user.behavior (6 partitions, replication=3, 30d retention)
# ✓ Created
# Creating: fluxcart.orders (3 partitions, replication=3, 90d retention)
# ✓ Created
# ... more topics ...
# All topics created successfully.
```

---

#### **Phase 3: Data Pipeline** (120+ seconds, runs in parallel)

**Terminal 1 — Run Complete Pipeline**:
```bash
python3 run_pipeline.py
# Output shows 4 components running simultaneously:

[producer] Initializing Kafka producer...
[producer] Connected to logical cluster.

[METRICS] Rate: 50.3 evt/sec | Sent: 503 | Failed: 0
[METRICS] Behavior: 326 | Orders: 126 | Payments: 51

[fluxcart-analytics] Consumer Initialized
[fluxcart-analytics] Subscribing to: ['fluxcart.user.behavior', 'fluxcart.orders']

[fluxcart-analytics] ══ ANALYTICS WINDOW (10s) ═════════════
[fluxcart-analytics]   Behavior Events: 450
[fluxcart-analytics]   Orders: 113
[fluxcart-analytics]   Revenue: Rs. 382,450

[fluxcart-fraud] ══ FRAUD WINDOW (10s) ═════════════
[fluxcart-fraud]   Payments: 58
[fluxcart-fraud]   Alerts raised: 3

[fluxcart-inventory] ══ INVENTORY WINDOW (10s) ═════════════
[fluxcart-inventory]   Orders: 141
[fluxcart-inventory]   Units ordered: 187
```

**Let this run for at least 120 seconds (2 minutes) to generate sufficient data.**

---

#### **Phase 4: Snowflake Export** (parallel with Phase 3)

**Terminal 2 — Run Exporter** (in new terminal):
```bash
python3 bi_integration/export.py
# Output (every 60 seconds):

[snowflake] Initializing exporters...
[snowflake] Starting AnalyticsExporter
[snowflake] Starting FraudExporter
[snowflake] Starting InventoryExporter

[snowflake] ── Batch 1 (60s) ──────────────────────────
  ❄️  Pushed 60 rows to ANALYTICS_SUMMARY
  ❄️  Pushed 15 fraud alerts to FRAUD_ALERTS
  ❄️  Pushed 45 inventory rows to INVENTORY_SUMMARY
[snowflake] CSV backups written to ./bi_integration/data/

[snowflake] ── Batch 2 (60s) ──────────────────────────
  ❄️  Pushed 65 rows to ANALYTICS_SUMMARY
  ...
```

---

#### **Phase 5: dbt Transformations**

**Terminal 1 (after producer finishes) OR new Terminal 3**:

```bash
# Navigate to dbt project
cd shopstream

# Test Snowflake connection
dbt debug
# Output: ✓ Connection test passed

# Run all models
dbt run
# Output:
# Running with dbt 1.11.7
# ...
# Creating view model DBT_DEV.stg_analytics
# ✓ Created view stg_analytics
# Creating view model DBT_DEV.stg_fraud
# ✓ Created view stg_fraud
# Creating view model DBT_DEV.stg_inventory
# ✓ Created view stg_inventory
# Creating table model DBT_DEV.mart_business_health
# ✓ Created table mart_business_health
#
# Done. 4 models built successfully.
```

**Generate dbt documentation**:
```bash
dbt docs generate
# Output:
# Compiled 4 models
# Compiled documentation

dbt docs serve
# Output: Serving docs at http://localhost:8000
```

Open http://localhost:8000 in browser to view:
- Model lineage graph
- Column descriptions
- Data types
- Source definitions

---

#### **Phase 6: Streamlit Dashboard** (optional visualization)

**Terminal 3 (or new terminal)**:
```bash
python3 streamlit_pipeline.py
# Output:
#   You can now view your Streamlit app in your browser.
#   Local URL: http://localhost:8501
```

Open http://localhost:8501 to see live dashboard with charts.

---

### Timeline Summary

```
T + 0min    → Start Kafka cluster (docker compose up -d)
T + 1min    → Create topics (python3 setup_topics.py)
T + 1.5min  → Start pipeline (python3 run_pipeline.py)
T + 2min    → Start exporter (python3 bi_integration/export.py)
T + 3min    → dbt run (shopstream/)
T + 3.5min  → dbt docs serve
T + 4min    → streamlit run streamlit_pipeline.py (optional)

T + 5min    → All systems running, data flowing end-to-end
```

---

### Common Issues & Solutions

**Issue**: "Connection refused" from producer
```
Solution: Ensure Kafka started: docker compose ps (all should be "Up")
          If not: docker compose down -v && docker compose up -d
```

**Issue**: "Topic does not exist"
```
Solution: Run python3 setup_topics.py before running producer
```

**Issue**: Snowflake push fails with "Invalid credentials"
```
Solution: Check SNOW_CONFIG in bi_integration/export.py
          Ensure account, user, password are correct
```

**Issue**: dbt run fails with "Schema does not exist"
```
Solution: Create DBT_DEV schema in Snowflake manually, or
          Change dbt profile to use existing schema (e.g., RAW)
```

---

## MONITORING & DASHBOARD

### Metrics Available

#### Real-Time Console Metrics (Producer)
- Events sent per second (rate)
- Total messages delivered vs failed
- Distribution by topic
- Distribution by partition (shows load balancing)

#### Consumer Window Reports (every 10 seconds)

**Analytics Consumer**:
- Behavior event count
- Action breakdown (view, search, add_to_cart, ...)
- Top products and categories
- Device and country distribution
- Order status distribution
- Window revenue

**Fraud Consumer**:
- Payment count and status distribution
- Fraud alerts raised (by severity level)
- Failed payment count
- Order cancellation rate

**Inventory Consumer**:
- Order count and status breakdown
- Units ordered/delivered/cancelled
- Top products and categories
- Warehouse activity distribution

#### Snowflake Data (via BI Tools)

**ANALYTICS_SUMMARY** (every 60 seconds):
- Timestamp
- Behavior event count
- Order count
- Total revenue

**FRAUD_ALERTS**:
- Alert ID, timestamp, user
- Risk level (HIGH/MEDIUM/LOW)
- Rule triggered
- Alert amount

**INVENTORY_SUMMARY**:
- Units ordered/delivered/cancelled per window
- Top products and categories
- Warehouse activity

#### dbt Models (in Snowflake)

**stg_analytics** (View):
- Cleaned and typed analytics data
- Ready for downstream analysis

**stg_fraud** (View):
- Typed fraud alert data

**stg_inventory** (View):
- Typed inventory data

**mart_business_health** (Table):
- Daily aggregations
- KPI calculations (net revenue, stock-to-behavior ratio)
- Key business metrics

### Streamlit Dashboard Features

**KPI Cards** (top row):
```
Total Behavior Events  |  Total Revenue  |  Total Fraud Alerts  |  Fulfillment Rate
```

**Revenue Over Time** (line chart):
- X-axis: timestamp
- Y-axis: cumulative or period revenue
- Hover for exact values

**Fraud Alerts Table** (color-coded):
```
RED    = HIGH risk
YELLOW = MEDIUM risk
GREEN  = LOW risk
```

**Top Products** (bar chart):
- Descending order by order count

**Warehouse Activity** (bar chart):
- Orders per warehouse

**Fulfillment Rate** (line chart):
- (delivered + shipped) / total orders

**Order Status Breakdown** (pie chart):
- Visual split of placed, confirmed, shipped, delivered, cancelled

---

## DATA QUALITY & TESTING

### Potential dbt Tests (if configured)

```sql
-- Check for NULLs
{{ not_null('event_at') }}

-- Check for uniqueness
{{ unique('alert_id') }}

-- Check for relationships
{{ relationships(
    column_name='user_id',
    to=source('sources', 'users'),
    field_name='user_id'
) }}

-- Custom SQL test
SELECT * FROM {{ ref('mart_business_health') }}
WHERE stock_to_behavior_ratio < 0
```

### Manual Data Validation

**Query analytics window data**:
```sql
SELECT * FROM KAFKA_DB.DBT_DEV.stg_analytics
ORDER BY event_at DESC
LIMIT 100;
```

**Check fraud detection**:
```sql
SELECT risk_level, COUNT(*) as alert_count
FROM KAFKA_DB.DBT_DEV.stg_fraud
GROUP BY risk_level;
```

**Inventory reconciliation**:
```sql
SELECT 
    SUM(units_ordered) as total_ordered,
    SUM(units_delivered) as total_delivered,
    SUM(units_cancelled) as total_cancelled
FROM KAFKA_DB.DBT_DEV.stg_inventory;
```

---

## TROUBLESHOOTING GUIDE

### Producer Issues

**No messages sent**:
- Check Kafka running: `docker compose ps`
- Check broker connectivity: `docker compose logs broker-1 | grep error`

**High failure rate**:
- Check broker logs: `docker compose logs`
- Reduce producer rate: modify `EVENTS_PER_SECOND` in config.py

### Consumer Issues

**Consumer lags (falling behind producer)**:
- Increase consumer threads (modify consumer implementation)
- Check process() function performance
- Monitor network latency to Kafka

**Duplicate messages**:
- Consumer crashed before offset commit
- Restart consumer, some messages will be reprocessed (normal)

**Dead letter topic growing**:
- Invalid JSON or schema mismatch in events
- Check logs: `[group_id] Sending to dead letter: ...`

### Snowflake Issues

**Connection timeout**:
- Verify account ID: SVHBWDV-PS62195 (check with Snowflake admin)
- Check network: ping `<account>.snowflakecomputing.com`

**Table already exists**:
- `write_pandas(..., auto_create_table=True)` only creates if missing
- If table structure wrong, drop and re-create:
  ```sql
  DROP TABLE KAFKA_DB.RAW.ANALYTICS_SUMMARY;
  ```

**Permission denied**:
- Verify KAFKA_ROLE has USAGE on warehouse
- Check role permissions: `SHOW GRANTS TO ROLE KAFKA_ROLE;`

### dbt Issues

**Models not found**:
- Check dbt_project.yml `model-paths`
- Run: `dbt parse` to validate syntax

**Incremental model issues**:
- If staging models are views, can't use incremental logic
- Use `materialized: 'table'` for incremental loads

**Documentation not generating**:
- Ensure all models have valid SQL syntax
- Add `description:` in YAML schema if needed

---

## CONCLUSION

This pipeline demonstrates a production-grade data architecture:

1. **Kafka** as the central nervous system for real-time events
2. **Python** for business logic (fraud detection, aggregations)
3. **Snowflake** as the scalable analytical store
4. **dbt** for version-controlled transformations
5. **Visualization** tools (Streamlit, dbt Docs) for insights

Every component is independent, scalable, and can be monitored or replaced independently. The 3-partition/3-broker architecture survives single failures. Manual offset commits ensure no message loss.

### Next Steps for Production

- Add data quality tests (dbt test)
- Implement schema validation (Avro/Protobuf instead of JSON)
- Auto-scaling for high-volume topics
- Multi-zone Snowflake clusters for geo-redundancy
- BI tool integration (Tableau, Looker, Power BI)
- Alert thresholds for SLA monitoring

---

**Documentation Version**: 1.0  
**Last Updated**: March 17, 2026  
**Maintained By**: Data Engineering Team

