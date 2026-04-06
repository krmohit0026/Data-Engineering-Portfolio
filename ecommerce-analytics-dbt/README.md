# E-Commerce DBT Pipeline Documentation

## Project Overview

**Project Name:** e_comm_project  
**Version:** 1.0.0  
**Purpose:** A complete data transformation pipeline for e-commerce data using DBT (Data Build Tool) and Snowflake, implementing the medallion architecture pattern for data quality and organization.

---

## Architecture Overview

The pipeline follows the **Medallion Architecture** (also known as Bronze-Silver-Gold architecture):

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA FLOW ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SOURCE        BRONZE LAYER       SILVER LAYER  GOLD LAYER   │
│  (Raw S3)      (Raw Tables)       (Staging)     (Analytics)  │
│                                                               │
│  S3 Bucket ───────> RAW Schema ───────> Staging ──────> DIM  │
│  (CSV Files)      (9 Tables)       Models      & FCT Tables   │
│                   in Snowflake    (Cleansed)    (Business    │
│                                                   Logic)      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Pipeline Stages Breakdown

### Stage 1: Data Ingestion - AWS S3 Setup
**Objective:** Prepare raw data in cloud storage

- **Action:** Created S3 bucket to store source data
- **Data Volume:** 9 CSV files uploaded
- **Purpose:** Central repository for raw e-commerce data

**Data Sources (9 CSV Files):**
1. RAW_CATEGORY - Product categories
2. RAW_CUSTOMERS - Customer information
3. RAW_GEOLOCATION - Geographic data
4. RAW_ORDER_ITEMS - Individual items in orders
5. RAW_ORDER_PAYMENTS - Payment transaction details
6. RAW_ORDER_REVIEWS - Customer reviews
7. RAW_ORDERS - Order header information
8. RAW_PRODUCTS - Product catalog
9. RAW_SELLERS - Seller information

---

### Stage 2: Snowflake Infrastructure Setup
**Objective:** Create a Snowflake environment with proper permissions and structure

**Created Resources:**

| Resource | Details |
|----------|---------|
| **Database** | `O_LIST_DB` |
| **Schema** | `RAW` (Bronze layer) |
| **Warehouse** | Compute cluster for query execution |
| **Role** | Custom role with permissions |
| **User** | DBT service account |
| **Permissions** | Account Admin access for comprehensive operations |

**Permissions Granted:**
- Database creation and modification
- Schema management
- Table creation and data loading
- Role and user management
- Warehouse operations

---

### Stage 3: Data Loading - S3 to Snowflake
**Objective:** Load raw CSV data into Snowflake bronze layer

**Method:** COPY Command (Snowflake)

**Process:**
```sql
COPY INTO table_name 
FROM @s3_stage/path/to/file.csv
FILE_FORMAT = csv_format
```

**Result:** 9 raw tables created in `O_LIST_DB.RAW` schema
- Tables are exact copies of S3 CSV files
- Serves as single source of truth for raw data
- Enables historical tracking and change management

---

### Stage 4: DBT Initialization & Configuration
**Objective:** Set up DBT project for transformation management

**Setup Steps Executed:**

1. **DBT Initialization**
   ```bash
   dbt init e_comm_project
   ```
   - Created project structure
   - Generated dbt_project.yml configuration
   - Set up profiles.yml for Snowflake connection

2. **Snowflake Connection**
   - Connected DBT to Snowflake warehouse
   - Configured authentication
   - Set development and production schemas

3. **Validation**
   ```bash
   dbt debug
   ```
   - Verified Snowflake connection
   - Confirmed all dependencies
   - Validated configuration

---

### Stage 5: DBT Project Structure
**Objective:** Organize transformation logic using medallion architecture

**Folder Creation:**
```
models/
├── staging/      (Silver Layer - Cleansing & Standardization)
├── dim/          (Gold Layer - Dimensional Tables)
├── fct/          (Gold Layer - Fact Tables)
└── sources.yml   (Source definitions)
```

**Purpose of Each Layer:**
- **Staging:** Direct transformation of raw data, simple selections and data type conversions
- **Dimensions:** Slowly changing dimensions, business entities (Orders, Products)
- **Facts:** Aggregated metrics and detailed transactional records

---

## Data Models

### Model Materialization Strategy

| Layer | Type | Purpose |
|-------|------|---------|
| **Staging** | VIEW | Ephemeral transformations, not stored |
| **Dimensions** | TABLE | Slower change rate, frequently joined |
| **Facts** | TABLE | High-volume transaction data |

### Source Definitions (`sources.yml`)

**Raw Tables (Bronze Layer):**

All tables are accessed from the `RAW` schema in `O_LIST_DB`:

```yaml
sources:
  - name: e_comm_project
    schema: raw
    tables:
      - name: r_CATEGORY          → identifier: RAW_CATEGORY
      - name: r_CUSTOMERS         → identifier: RAW_CUSTOMERS
      - name: r_GEOLOCATION       → identifier: RAW_GEOLOCATION
      - name: r_ORDER_ITEMS       → identifier: RAW_ORDER_ITEMS
      - name: r_ORDER_PAYMENTS    → identifier: RAW_ORDER_PAYMENTS
      - name: r_ORDER_REVIEWS     → identifier: RAW_ORDER_REVIEWS
      - name: r_ORDERS            → identifier: RAW_ORDERS
      - name: r_PRODUCTS          → identifier: RAW_PRODUCTS
      - name: r_SELLERS           → identifier: RAW_SELLERS
```

---

## Transformation Models

### Silver Layer (Staging Models)

**Purpose:** Clean, validate, and standardize raw data

**Staging Models:**

#### `src_orders` - Order Data Cleansing
```sql
SELECT 
    CUSTOMER_ID,
    ORDER_APPROVED_AT,
    ORDER_DELIVERED_CARRIER_DATE,
    ORDER_DELIVERED_CUSTOMER_DATE,
    ORDER_ESTIMATED_DELIVERY_DATE,
    ORDER_ID,
    ORDER_PURCHASE_TIMESTAMP,
    ORDER_STATUS
FROM RAW_ORDERS
```
- **Output Type:** VIEW
- **Logic:** Direct selection with column renaming for clarity

#### `src_customers` - Customer Dimension Cleansing
- Direct transformation of RAW_CUSTOMERS
- Standardized column naming

#### `src_products` - Product Catalog Cleansing
- Raw product data filtered and formatted
- Maintains referential integrity with sellers

#### `src_geolocation` - Geographic Data
- Cleansed location information
- Standardized format

#### `src_order_items` - Order Line Items
- Individual item transactions
- Links orders to products

#### `src_sellers` - Seller Information
- Seller profile and location data

#### `src_order_payments` - Payment Transactions
- Payment method and amount details

#### `src_order_reviews` - Customer Reviews
- Review scores and comments

#### `src_categories` - Product Categories
- Category hierarchy and naming

---

### Gold Layer (Dimensional & Fact Models)

#### **Dimension Tables (DIM)**

##### `dim_orders` - Order Dimension
```sql
SELECT 
    CUSTOMER_ID,
    ORDER_APPROVED_AT,
    ORDER_DELIVERED_CUSTOMER_DATE,
    ORDER_ESTIMATED_DELIVERY_DATE,
    ORDER_ID,
    ORDER_PURCHASE_TIMESTAMP,
    INITCAP(TRIM(ORDER_STATUS)) AS ORDER_STATUS
FROM src_orders
```
- **Output Type:** TABLE
- **Business Logic:**
  - References staging layer for cleansed data
  - Capitalizes and trims order status for consistency
  - Tracks order lifecycle and delivery status
  - Used for order-level reporting

##### `dim_seller_products` - Product-Seller Relationship
- Links sellers to their product offerings
- Tracks product-seller dimensions
- Enables product-level analytics

---

#### **Fact Tables (FCT)**

##### `fct_cust_orders` - Customer Order Facts
```sql
WITH orders AS (
    SELECT CUSTOMER_ID, ORDER_APPROVED_AT, ORDER_ID, 
           ORDER_PURCHASE_TIMESTAMP, ORDER_STATUS
    FROM src_orders
),
cust AS (
    SELECT CUSTOMER_ID, CUSTOMER_ZIP_CODE_PREFIX
    FROM src_customers
)
SELECT DISTINCT 
    CUSTOMER_ID,
    CUSTOMER_ZIP_CODE_PREFIX,
    ORDER_ID,
    ORDER_STATUS
FROM orders o
JOIN cust c ON o.CUSTOMER_ID = c.CUSTOMER_ID
```
- **Output Type:** TABLE
- **Business Logic:**
  - Joins orders with customer location data
  - Enables geographic order analysis
  - Combines order and customer dimensions
  - Supports sales by location reporting

##### `fct_order_items` - Transaction-Level Facts
- Item-level transaction records
- Links orders to individual products
- Tracks quantities and prices

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Data Warehouse** | Snowflake | Latest |
| **Transformation Tool** | DBT (Data Build Tool) | 1.x |
| **Data Source** | AWS S3 | - |
| **Dependencies** | dbt_utils | 1.3.0 |
| **Version Control** | Git | - |
| **Development IDE** | VS Code | - |

---

## Project Configuration

### dbt_project.yml Settings

**Key Configuration:**

```yaml
name: 'e_comm_project'
version: '1.0.0'
profile: 'e_comm_project'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

models:
  e_comm_project:
    staging:
      +materialized: view      # Ephemeral transformations
    dim:
      +materialized: table     # Persistent dimensional data
    fct:
      +materialized: table     # Persistent fact data
```

---

## File Structure

```
e_comm_project/
├── dbt_project.yml              # Project configuration
├── packages.yml                 # Dependencies (dbt_utils)
├── package-lock.yml             # Locked dependency versions
├── README.md                     # Project readme
├── PIPELINE_DOCUMENTATION.md    # This file
│
├── models/
│   ├── sources.yml              # Raw table definitions
│   ├── staging/                 # Silver layer (Views)
│   │   ├── src_orders.sql
│   │   ├── src_customers.sql
│   │   ├── src_products.sql
│   │   ├── src_geolocation.sql
│   │   ├── src_order_items.sql
│   │   ├── src_order_payments.sql
│   │   ├── src_order_reviews.sql
│   │   ├── src_sellers.sql
│   │   └── src_categories.sql
│   ├── dim/                     # Gold layer - Dimensions (Tables)
│   │   ├── dim_orders.sql
│   │   └── dim_seller_products.sql
│   └── fct/                     # Gold layer - Facts (Tables)
│       ├── fct_cust_orders.sql
│       └── fct_order_items.sql
│
├── seeds/                       # Static lookup tables
│   └── order_placed.csv
│
├── snapshots/                   # Historical tracking
│   └── snap_cust.sql
│
├── macros/                      # Reusable SQL functions
│
├── tests/                       # Data quality tests
│
├── analyses/                    # Ad-hoc analysis queries
│
├── dbt_packages/                # Installed packages
│   └── dbt_utils/
│
├── logs/                        # DBT execution logs
│
└── target/                      # Build artifacts
    ├── manifest.json            # Project metadata
    ├── graph.gpickle            # DAG visualization
    ├── run_results.json         # Execution results
    ├── compiled/                # Compiled SQL
    └── run/                     # Execution logs
```

---

## Data Flow Summary

```
Step 1: Data Ingestion
└─────► S3 Bucket (9 CSV Files)

Step 2: Infrastructure Setup
└─────► Snowflake Database/Schema/Warehouse/User/Role

Step 3: Data Loading
└─────► 9 RAW Tables in O_LIST_DB.RAW (Bronze Layer)

Step 4: DBT Setup
└─────► Project Initialization & Connection Testing (dbt debug ✓)

Step 5: Silver Layer Transformation
└─────► 9 Staging Views (Cleansed & Standardized)
        └─ src_orders, src_customers, src_products, etc.

Step 6: Gold Layer Transformation
└─────► Dimension Tables (Persistent)
        ├─ dim_orders
        └─ dim_seller_products
        
        └─ Fact Tables (Persistent)
           ├─ fct_cust_orders
           └─ fct_order_items

Final: Ready for Analytics & Reporting
```

---

## Key Features

### ✅ Medallion Architecture
- **Bronze:** Raw tables (RAW schema) - exact copies of CSV files
- **Silver:** Staging views - cleaned and standardized data
- **Gold:** Dimension & Fact tables - business-ready analytics

### ✅ Data Quality
- Standardized formatting (INITCAP, TRIM functions)
- Referential integrity (primary/foreign key relationships)
- Documented source definitions

### ✅ Modularity
- Separate staging, dimension, and fact layers
- Easy to extend with new tables
- Clear separation of concerns

### ✅ Dependency Management
- dbt_utils package for common transformations
- Version-locked dependencies (package-lock.yml)
- Managed through dbt's ref() function

### ✅ Scalability
- Table materialization for dimension and fact tables
- View materialization for staging (memory efficient)
- Built-in DAG management

---

## Running the Pipeline

### Initial Setup
```bash
# Navigate to project directory
cd e_comm_project

# Activate virtual environment
./dbtenv/Scripts/activate

# Install dependencies
dbt deps

# Test connection
dbt debug
```

### Execute Transformations
```bash
# Run all models
dbt run

# Run specific model
dbt run --select model_name

# Run with fresh tables
dbt run --full-refresh

# Run staging layer only
dbt run --select path:models/staging
```

### Data Quality Testing
```bash
# Execute tests
dbt test

# Test specific model
dbt test --select model_name
```

### Generate Documentation
```bash
# Generate project docs
dbt docs generate

# Serve docs locally
dbt docs serve
```

---

## Dependencies & Packages

### Installed Packages
- **dbt_utils** (v1.3.0) - Utility macros for common SQL patterns

### Requirements
- Python 3.8+
- Snowflake account with appropriate permissions
- AWS S3 bucket with raw data files

---

## Performance Considerations

### Materialization Strategy
- **Staging Models (Views):** Reduces storage, computed on-demand
- **Dim/Fct Tables:** Persisted for faster analytics queries

### Warehouse Operations
- Snowflake warehouse handles compute
- Scaling based on query complexity
- COPY command optimized for bulk loading

---

## Future Enhancements

Potential additions to the pipeline:

1. **Data Quality Tests**
   - Not-null assertions
   - Uniqueness constraints
   - Referential integrity tests

2. **Incremental Models**
   - Incremental loading for fact tables
   - Reduced processing time

3. **Snapshots**
   - Historical tracking (already configured with snap_cust.sql)
   - Change Data Capture (CDC) patterns

4. **Monitoring & Logging**
   - Execution performance tracking
   - Error alerts and recovery

5. **Additional Analytics**
   - More dimensions (Product, Seller, Category hierarchies)
   - Aggregated facts (daily/monthly order summaries)
   - KPI calculations

6. **Documentation**
   - dbt docs with descriptions and relationships
   - Column-level documentation

---

## Contact & Support

For questions about this pipeline or to request enhancements, refer to the project's README.md or contact the data team.

---

*Documentation Version: 1.0*  
*Last Updated: March 2026*
