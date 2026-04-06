\# Data Engineering & Analytics Portfolio  
\> \*\*Ex-Amazon Data Analyst | MS in Data Engineering Student\*\*

Welcome to my technical portfolio. This repository showcases my transition from Data Analytics into \*\*Data Engineering\*\*, featuring end-to-end pipelines that leverage the Modern Data Stack to solve complex data challenges.

\---

\#\# 🛠️ Technical Stack  
\* \*\*Languages:\*\* Python (Pandas, Requests, PySpark), SQL (Expert)  
\* \*\*Streaming:\*\* Apache Kafka (Confluent, Docker Compose)  
\* \*\*Data Warehouse:\*\* Snowflake (Snowpipe, Tasks, RBAC)  
\* \*\*Transformation:\*\* dbt (Dimensional Modeling, Testing, Documentation)  
\* \*\*Cloud & DevOps:\*\* AWS (S3, EC2), Docker, Terraform (Basic)

\---

\#\# 🚀 Featured Projects

\#\#\# 1\. FluxCart: Real-Time E-Commerce Event Pipeline  
\*\*Tech:\*\* Kafka (3 Brokers), Python, Snowflake, dbt, Streamlit  
\* Built a high-throughput streaming architecture simulating 4 distinct event topics (User Behavior, Orders, Payments, Fraud).  
\* Implemented manual offset management in Python consumers to ensure zero data loss during ingestion to Snowflake.  
\* \*\*Key Achievement:\*\* Developed a real-time fraud detection trigger within the consumer logic to flag suspicious payment patterns.  
\* \[View Project Folder\](./fluxcart-pipeline)

\#\#\# 2\. Football ELT: API-to-Cloud Data Pipeline  
\*\*Tech:\*\* FastAPI, Kafka, AWS S3, Snowflake, dbt  
\* Architected an automated ELT pipeline fetching real-time match data from the Football-Data.org API.  
\* Streamed raw JSON to AWS S3 using Kafka as the central nervous system, later staging data into Snowflake.  
\* \*\*Key Achievement:\*\* Transformed raw nested JSON into a clean Star Schema (Fact\_Matches, Dim\_Teams) using dbt, including automated data quality tests.  
\* \[View Project Folder\](./football-pipeline)

\#\#\# 3\. E-Commerce Medallion Architecture (dbt Focus)  
\*\*Tech:\*\* Snowflake, dbt, AWS S3  
\* Implemented a classic \*\*Medallion Architecture\*\* (Bronze/Silver/Gold) to transform raw CSV data into analytics-ready Marts.  
\* Designed complex SQL transformations in dbt to handle historical tracking (SCD Type 2\) and customer behavior snapshots.  
\* \*\*Key Achievement:\*\* Established a rigorous testing framework in dbt ensuring referential integrity across 9+ core business tables.  
\* \[View Project Folder\](./ecomm-dbt-pipeline)

\---

\#\# 📈 Professional Background  
Previously a \*\*Data Analyst at Amazon\*\*, I specialized in SQL optimization and business intelligence. I am now combining that business acumen with engineering rigor to build scalable, automated data systems.

\---  
📫 \*\*Connect with me:\*\* \[LinkedIn\](https://www.linkedin.com/in/0209-1609-kumar-mohit/) |  
 \[Email\](mailto:krmohit0026@gmail.com)  
