Building a project like this is rarely a straight line. Documenting the "war stories" is actually what makes a README or a Portfolio project look professional—it shows you know how to debug and architect around real-world data issues.

Here is a structured **Challenges & Hurdles** section for your `README.md`.

---

## 🚧 Challenges & Hurdles

Building an end-to-end data pipeline from a live Football API to a Snowflake Data Warehouse presented several technical challenges. Below are the key hurdles faced and how they were overcome.

### 1. Semi-Structured Data Complexity (JSON Flattening)
**The Challenge:** The raw data arrived from the API as deeply nested JSON objects. Specifically, the league standings were nested within a `table` array inside a `raw_data` object. Standard SQL cannot query this directly.
**The Solution:** Leveraged Snowflake’s `LATERAL FLATTEN` function and `VARIANT` data types. We iterated through the JSON paths (`raw_data:table`) to transform nested arrays into a relational format (rows and columns) within dbt staging models.

### 2. Schema Mismatches & "Null" Records
**The Challenge:** Initial dbt runs resulted in `0 rows` in the final Marts, despite data existing in the Raw layer. This was due to subtle mismatches between the Python-ingested JSON structure and the dbt transformation paths (e.g., looking for `raw_data:raw_data:table` when the data was actually at `raw_data:table`).
**The Solution:** Performed manual "Path Probing" in Snowflake using direct SQL queries to verify the exact location of keys. Updated dbt staging models to use direct accessors, ensuring the data flow was restored.

### 3. Environment & Package Dependencies
**The Challenge:** Advanced transformations, such as generating unique Surrogate Keys for the `DIM_TEAMS` table, required external logic not found in standard SQL.
**The Solution:** Integrated the `dbt-utils` package. This required managing a `packages.yml` file and handling version control through `dbt deps` to ensure the project had the necessary "macros" to generate consistent hashes for team identification.

### 4. Database Reserved Keywords
**The Challenge:** During data validation, SQL queries failed with cryptic syntax errors when calculating row counts. 
**The Solution:** Identified that `ROWS` is a reserved keyword in Snowflake (used for window functions). Resolved this by aliasing columns as `row_count` or using double quotes, a critical lesson in Snowflake-specific SQL syntax.

### 5. Idempotency & Data Duplication
**The Challenge:** Re-running the S3-to-Snowflake `COPY INTO` command risked duplicating match records, which would skew league standings and goal averages.
**The Solution:** Implemented a controlled ingestion strategy using `FORCE = FALSE` for incremental loads and utilized dbt's `unique` tests to verify that `match_id` remained a primary key throughout the pipeline.

### 6. Ensuring Data Integrity (The "Football Math" Problem)
**The Challenge:** In sports data, it is easy for "dirty data" to enter the system (e.g., a team having more points than games played).
**The Solution:** Developed **Singular Data Tests** in dbt. We wrote custom SQL assertions to ensure that `Wins + Draws + Losses` always equaled `Total Games Played`, creating an automated guardrail for data quality.

---

### 💡 Pro-Tip for your Documentation:
When you put this in your `.md` file, you might want to add a "Key Learnings" section afterward, mentioning things like:
* **The Medallion Architecture:** Why you chose to separate data into Staging, Intermediate, and Marts.
* **Infrastructure as Code:** How dbt allowed you to manage your entire Snowflake schema using just SQL and YAML.
