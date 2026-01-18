from src.extraction import Extraction
from src.load_to_postgres import PostgresConnector
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/extraction_and_loading.log', mode = 'w'),
        logging.StreamHandler()
    ],
    force=True
)

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': 'postgres_docker',
    'port': 5432}

def main(): #load per run
    logging.info("="*80)
    logging.info("Extraction Starting...")
    logging.info("="*80)
    extraction = Extraction("https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page")
    taxi_type_per_run, final_combined = extraction.extract_all_taxi_data(extraction.url)
    
    if not final_combined:
        logging.error(f"Extraction Failed!")
    
    else:
        logging.info("Extraction Success!")

    logging.info("="*80)
    logging.info("Loading to Postgres Starting...")
    logging.info("="*80)

    logging.info("Loading per run_id...")
    pg = PostgresConnector(**DB_CONFIG)

    runs_by_id = {} #{1: {'green': df, 'yellow': df}, 2:{'green': df, 'yellow': df}}
    for key, df in taxi_type_per_run.items():
        #taxi_type_per_run= {yellow_1:df, green_1:df}
        parts = key.split("_")
        taxi_type = parts[0]
        run_id = int(parts[1])

        if run_id not in runs_by_id:
            runs_by_id[run_id] = {}

        runs_by_id[run_id][taxi_type] = df

    for run_id in sorted(runs_by_id.keys()): #run run_id 1-7
        logging.info(f"Loading run {run_id}")

        for taxi_type, df in runs_by_id[run_id].items():
            if df.empty:
                logging.warning(f"Empty dataframe for {taxi_type}_{run_id}")
                continue

            table_name = f"nyc_{taxi_type}_2025-01"
            pg.load(table_name, df) 
            logging.info(f"{taxi_type}: Run {run_id} Loaded!")
    pg.close()
    logging.info("="*80)
    logging.info("Loading to Postgres Completed...")
    logging.info("="*80)

if __name__ == "__main__":
    main()






    

