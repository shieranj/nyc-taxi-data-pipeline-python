# ELT Project 1

# NYC Taxi Python ELT Pipeline

This project demonstrates an end-to-end ELT (Extract, Load, Transform) data
pipeline built using **pure Python (3.12.10)**. It processes NYC Green and
Yellow Taxi trip data with daily filtering logic, automated aggregation,
notifications, and logging.

This project represents my **Python development progress after approximately
3 weeks of focused, hands-on learning**, applying foundational Python concepts
to a real-world data engineering use case.

---

## Project Overview

The pipeline extracts NYC Taxi trip data, filters records by **day of week**,
loads raw data into PostgreSQL, performs data transformations and aggregations,
and sends automated notifications via email and Discord. Execution is
orchestrated using **shell scripts and cron**, without workflow orchestration
tools such as Airflow.

---

## Tech Stack

- **Language**: Python 3.12.10  
- **Data Processing**: pandas  
- **Database**: PostgreSQL  
- **Orchestration**: Shell script + cron  
- **Containerization**: Docker & Docker Compose  
- **Notifications**: Email (SMTP) & Discord Webhook  
- **Logging**: File-based logging  

---

## Data Source

- NYC TLC Trip Record Data
  - Yellow Taxi Trip Records
  - Green Taxi Trip Records

---

## Pipeline Flow

1. **Extraction**
   - Download NYC Taxi data for January 2025
   - Filter data based on **day of week**
   - Validate file existence and data integrity

2. **Loading**
   - Load raw filtered data into PostgreSQL
   - Store extracted files locally for traceability

3. **Transformation**
   - Data cleansing and standardization
   - Aggregation (e.g. trip counts, summaries)

4. **Notification**
   - Send aggregation summaries to Discord
   - Export aggregation results to CSV and send via email

5. **Logging**
   - Execution logs captured per script
   - Consolidated reporting log stored in `/logs`

---

## Project Structure
├── scripts/
│   ├── extraction_and_loading.sh
│   ├── transformation_and_notification.sh
├── src/
│   ├── extraction_and_loading.py
│   ├── transformation_and_notification.py
│   ├── extraction.py
│   ├── load_to_postgres.py
│   ├── notification.py
│   ├── transformation.py
├── logs/
│   ├── extraction_and_loading.log
│   ├── transformation_notification.log
│   └── report.log
├── data/
│   ├── raw/
│   ├── aggregation/
├── .env
├── docker-compose.yaml
├── dockerfile.ubuntu
├── requirements.txt
└── README.md