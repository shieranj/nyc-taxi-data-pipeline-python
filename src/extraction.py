import requests
from bs4 import BeautifulSoup
import logging
import os
import pandas as pd
from datetime import datetime

#create folders for log files and raw data
os.makedirs("logs", exist_ok=True)
OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

#logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/extraction_and_loading.log', mode = 'w'),
        logging.StreamHandler()
    ],
    force=True
)

# filter by day of week
FILTER_CONFIGS = [
    {'run_id': 1, 'day_of_week': 0, 'description': 'Monday'},
    {'run_id': 2, 'day_of_week': 1, 'description': 'Tuesday'},
    {'run_id': 3, 'day_of_week': 2, 'description': 'Wednesday'},
    {'run_id': 4, 'day_of_week': 3, 'description': 'Thursday'},
    {'run_id': 5, 'day_of_week': 4, 'description': 'Friday'},
    {'run_id': 6, 'day_of_week': 5, 'description': 'Saturday'},
    {'run_id': 7, 'day_of_week': 6, 'description': 'Sunday'},
]

class Extraction:
  """
  webscrape 
  read parquet into dataframe
  filter by day of week
  add metadata column
  """
  def __init__(self, url):
    self.url = url

  def get_links(self):
    """webscrape for parquet link"""
    try:
      resp = requests.get(self.url)
      resp.raise_for_status()  #raise error if request return unsuccessful status code
      soup = BeautifulSoup(resp.text, "html.parser")

      links = []
      for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        if ("yellow" in href or "green" in href) and "2025-01" in href and href.endswith(".parquet"):
          links.append(href)
          logging.info(f"Found link: {href}")

      if not links:
        logging.warning("No matching links found.")

      return links

    except requests.exceptions.RequestException as e:
      logging.error(f"Error connecting to the URL: {e}")
      raise
    except Exception as e:
      logging.error(f"Unexpected error: {e}")
      raise

  def read_parquet(self, links):
    """save parquet file as df"""
    dataframes = {}
    for link in links:
      if "yellow" in link:
        taxi_type = "yellow"
      else:
        taxi_type = "green"
      logging.info(f"Reading {taxi_type} taxi data from {link}...")
      try:
        df = pd.read_parquet(link)
        dataframes[taxi_type] = df
        logging.info(f"Successfully read {taxi_type} taxi data from {link}, total: {len(df)} rows")
      except Exception as e:
        logging.error(f"Error reading {taxi_type} taxi data from {link}: {e}")
    return dataframes

  def filter_by_day_of_week(self, dataframes, day_of_week):
    filtered_dataframes = {}
    try:
      for taxi_type, df in dataframes.items():
        pickup_column = "tpep_pickup_datetime" if taxi_type == "yellow" else "lpep_pickup_datetime"
        if pickup_column not in df:
          logging.warning(f"Column {pickup_column} not found in {taxi_type} taxi data.")
          continue
        
        df_copy = df.copy() #best practice, create copy instead of manipulating original df
        df_copy[pickup_column] = pd.to_datetime(df_copy[pickup_column], errors='coerce')

        # remove rows if pickup columns is null
        invalid_count = df_copy[pickup_column].isnull().sum()
        if invalid_count > 0:
          logging.warning(f"Found {invalid_count} invalid {pickup_column} values in {taxi_type} taxi data.")
          df_copy.dropna(subset=[pickup_column], inplace=True)

        # filter by day_of_week
        filtered_df = df_copy[df_copy[pickup_column].dt.dayofweek == day_of_week].copy()
        if filtered_df.empty:
          logging.warning(f"No records found for {taxi_type} taxi on day_of_week={day_of_week}")
        else:
          filtered_dataframes[taxi_type] = filtered_df
          logging.info(f"Filtered {taxi_type} taxi: {len(filtered_df):,} records for day_of_week={day_of_week}")

    except Exception as e:
      logging.error(f"Error filtering dataframes: {e}")
    return filtered_dataframes
  
  def metadata_addition(self, dataframes, run_id):
    """Add metadata columns to dataframes and return modified dataframes"""
    try:
      for taxi_type, df in dataframes.items():
        df["run_id"] = run_id
        df["extraction_timestamp"] = pd.Timestamp.now()
        logging.info(f"Added metadata to {taxi_type} taxi data (run_id={run_id})")

    except Exception as e:
      logging.error(f"Error adding metadata to dataframes: {e}")
    
    return dataframes #returns modified dataframes
  
  def save_as_csv(self, dataframes, run_id, description):
    try:
      timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

      for taxi_type, df in dataframes.items():
        if df.empty:
          logging.warning("Skipping empty dataframes for {taxi_type}")
          continue

        filename = f"{OUTPUT_DIR}/{taxi_type}_run{run_id}_{description.lower()}_{timestamp}.csv"
        df.to_csv(filename, index = False)
        logging.info(f"Saved {len(df)} records to {filename}")

    except Exception as e:
      logging.error(f"Failed to save {taxi_type} for day {description} ")

  def extract_all_taxi_data(self,url):
    extraction = Extraction(url)
    links = extraction.get_links()
    original_dataframes = extraction.read_parquet(links)
    
    taxi_type_per_run = {} #{yellow_0: df, yellow_1: df}
    final_combined = {} #{yellow: df, green: df}

    try:
      for config in FILTER_CONFIGS: #extraction done 7 times (day of week)
        run_id = config['run_id']
        day_of_week = config['day_of_week']
        description = config['description']

        filtered_dataframes = extraction.filter_by_day_of_week(original_dataframes, day_of_week)
        filtered_dataframes = extraction.metadata_addition(filtered_dataframes, run_id)
        extraction.save_as_csv(filtered_dataframes, run_id, description)

        for taxi_type, df in filtered_dataframes.items():
          key = f"{taxi_type}_{run_id}"
          taxi_type_per_run[key] = df

      type_group = {} #{"yellow": [df1, df2], "green": [df3]}
      for key, df in taxi_type_per_run.items():
        taxi_type = key.split("_")[0]
        type_group.setdefault(taxi_type, []).append(df)

      for taxi_type, dfs in type_group.items():
        if dfs:
          final_combined[taxi_type] = pd.concat(dfs, ignore_index = True)
          logging.info(f"Combined {taxi_type}: {len(final_combined[taxi_type])} rows")

        else:
          logging.warning(f"No data combined for {taxi_type}!")

    except Exception as e:
      logging.error(f"Error at extract_all_taxi_data function: {e}")

    return taxi_type_per_run, final_combined #used in loading
