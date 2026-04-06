import sys
import os
import time
import threading
import json
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from datetime import datetime
from collections import defaultdict
from confluent_kafka import Consumer, KafkaError

# Add project root to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_USER_BEHAVIOR,
    TOPIC_ORDERS,
    TOPIC_FRAUD_ALERTS,
    consumer_config,
)

# =============================================================================
# 1. SNOWFLAKE CONFIGURATION
# =============================================================================
SNOW_CONFIG = {
    "user": "KAFKA_USER",
    "password": "KAFKAPassword2602",
    "account": "SVHBWDV-PS62195", # <--- UPDATE THIS (e.g. org-account)
    "warehouse": "KAFKA_WH",
    "database": "KAFKA_DB",
    "schema": "RAW",
    "role": "KAFKA_ROLE"
}

EXPORT_INTERVAL_SECONDS = 60

# =============================================================================
# 2. SHARED STATE (Memory Buffers)
# =============================================================================
analytics_rows = []
fraud_rows     = []  # Consistent name used throughout
inventory_rows = []
state_lock     = threading.Lock()

# =============================================================================
# 3. SNOWFLAKE PUSH FUNCTION
# =============================================================================
def push_to_snowflake(data_list, table_name):
    """Writes a batch of dictionaries to Snowflake as a table."""
    if not data_list:
        print(f"  [snowflake] No new data to upload for {table_name}")
        return

    try:
        conn = snowflake.connector.connect(**SNOW_CONFIG)
        df = pd.DataFrame(data_list)
        
        # Standardize columns to Uppercase for Snowflake
        df.columns = [c.upper() for c in df.columns]

        # Use high-speed write_pandas
        success, nchunks, nrows, _ = write_pandas(
            conn=conn, 
            df=df, 
            table_name=table_name.upper(), 
            auto_create_table=True
        )

        if success:
            print(f"  ❄️  Snowflake: Successfully pushed {nrows} rows to {table_name.upper()}")
        
        conn.close()
    except Exception as e:
        print(f"  ❌ Snowflake Error: {e}")

# =============================================================================
# 4. EXPORTER CLASSES (Kafka Consumers)
# =============================================================================

class AnalyticsExporter:
    WINDOW_SECONDS = 10
    GROUP_ID = "fluxcart-snowflake-analytics"

    def __init__(self):
        cfg = consumer_config(self.GROUP_ID, offset_reset="earliest")
        self.consumer = Consumer(cfg)
        self.consumer.subscribe([TOPIC_USER_BEHAVIOR, TOPIC_ORDERS])
        self._reset_window()
        self.window_start = time.time()
        self.running = True

    def _reset_window(self):
        self.behavior_count  = 0
        self.action_counts   = defaultdict(int)
        self.product_counts  = defaultdict(int)
        self.category_counts = defaultdict(int)
        self.order_count     = 0
        self.order_totals    = []

    def run(self):
        while self.running:
            msg = self.consumer.poll(timeout=1.0)
            if msg is not None and not msg.error():
                try:
                    event = json.loads(msg.value().decode("utf-8"))
                    if msg.topic() == TOPIC_USER_BEHAVIOR:
                        self.behavior_count += 1
                        self.action_counts[event.get("action", "unknown")] += 1
                        self.product_counts[event.get("product_id", "unknown")] += 1
                        self.category_counts[event.get("category", "unknown")] += 1
                    elif msg.topic() == TOPIC_ORDERS:
                        self.order_count += 1
                        self.order_totals.append(event.get("order_total", 0))
                except: pass

            if time.time() - self.window_start >= self.WINDOW_SECONDS:
                self._flush_window()
        self.consumer.close()

    def _flush_window(self):
        now = datetime.utcnow().isoformat()
        row = {
            "timestamp": now, 
            "behavior_events": self.behavior_count,
            "order_events": self.order_count,
            "total_revenue": round(sum(self.order_totals), 2)
        }
        with state_lock:
            analytics_rows.append(row)
        self._reset_window()
        self.window_start = time.time()

    def stop(self): self.running = False

class FraudExporter:
    GROUP_ID = "fluxcart-snowflake-fraud"
    def __init__(self):
        cfg = consumer_config(self.GROUP_ID, offset_reset="earliest")
        self.consumer = Consumer(cfg)
        self.consumer.subscribe([TOPIC_FRAUD_ALERTS])
        self.running = True

    def run(self):
        while self.running:
            msg = self.consumer.poll(timeout=1.0)
            if msg is not None and not msg.error():
                try:
                    alert = json.loads(msg.value().decode("utf-8"))
                    row = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "alert_id": alert.get("alert_id", ""),
                        "rule": alert.get("rule", ""),
                        "user_id": alert.get("user_id", ""),
                        "amount": alert.get("amount", 0)
                    }
                    with state_lock:
                        fraud_rows.append(row)
                except: pass
        self.consumer.close()

    def stop(self): self.running = False

class InventoryExporter:
    WINDOW_SECONDS = 10
    GROUP_ID = "fluxcart-snowflake-inventory"
    def __init__(self):
        cfg = consumer_config(self.GROUP_ID, offset_reset="earliest")
        self.consumer = Consumer(cfg)
        self.consumer.subscribe([TOPIC_ORDERS])
        self._reset_window()
        self.window_start = time.time()
        self.running = True

    def _reset_window(self):
        self.order_count = 0
        self.units_ordered = 0

    def run(self):
        while self.running:
            msg = self.consumer.poll(timeout=1.0)
            if msg is not None and not msg.error():
                try:
                    event = json.loads(msg.value().decode("utf-8"))
                    self.order_count += 1
                    self.units_ordered += event.get("quantity", 1)
                except: pass
            if time.time() - self.window_start >= self.WINDOW_SECONDS:
                self._flush_window()
        self.consumer.close()

    def _flush_window(self):
        now = datetime.utcnow().isoformat()
        row = {"timestamp": now, "orders": self.order_count, "units": self.units_ordered}
        with state_lock:
            inventory_rows.append(row)
        self._reset_window()
        self.window_start = time.time()

    def stop(self): self.running = False

# =============================================================================
# 5. THE EXPORT LOOP
# =============================================================================

def export_loop(exporters):
    cycle = 0
    print(f"\n[export] Cloud Sync active. Interval: {EXPORT_INTERVAL_SECONDS}s")
    try:
        while True:
            time.sleep(EXPORT_INTERVAL_SECONDS)
            cycle += 1
            
            with state_lock:
                # Create snapshots of the lists and clear them immediately
                a_batch = list(analytics_rows)
                f_batch = list(fraud_rows)
                i_batch = list(inventory_rows)
                
                analytics_rows.clear()
                fraud_rows.clear()
                inventory_rows.clear()

            print(f"\n[export] Cycle {cycle:03d} @ {datetime.now().strftime('%H:%M:%S')}")
            push_to_snowflake(a_batch, "ANALYTICS_SUMMARY")
            push_to_snowflake(f_batch, "FRAUD_ALERTS")
            push_to_snowflake(i_batch, "INVENTORY_SUMMARY")

    except KeyboardInterrupt:
        print("\n[export] Stopping...")
        for exp, name in exporters: exp.stop()

# =============================================================================
# 6. MAIN ENTRY POINT
# =============================================================================

def main():
    analytics_exp = AnalyticsExporter()
    fraud_exp     = FraudExporter()
    inventory_exp = InventoryExporter()
    
    exporters = [(analytics_exp, "analytics"), (fraud_exp, "fraud"), (inventory_exp, "inventory")]

    threads = []
    for exp, name in exporters:
        t = threading.Thread(target=exp.run, daemon=True)
        t.start()
        threads.append(t)
    
    export_loop(exporters)

if __name__ == "__main__":
    main()