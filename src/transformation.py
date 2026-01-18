import pandas as pd
import logging
import os
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/transformation_and_notifications.log', mode = 'w'),
        logging.StreamHandler()
    ],
    force=True
)


def read_from_postgres(dbname, user, password,  host = "localhost", port = 5432):
    """ Connect to postgres & save as df"""
    final_combined={} #{yellow:df, green:df}

    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        logging.info(f"Connected to Postgres {dbname}")
        
        for taxi_type in ["yellow","green"]:
            table_name = f"nyc_{taxi_type}_2025-01"

            query = f'SELECT * FROM "{table_name}"'

            logging.info(f"Querying from table {table_name}")
            df = pd.read_sql(query, conn)

            final_combined[table_name] = df
            logging.info(f"Saving dataframe from table {table_name}")

        conn.close()
        logging.info("Connection to Postgres closed!")

    except Exception as e:
        logging.error(f"Error reading from Postgres. Error {e}")
        raise    

    return final_combined

class Transformation:
    """
    clean columns: standardize columns, drop empty and Y/N columns
    clean values: fill in empty rows, 
    """
    def __init__(self,final_combined):
        self.final_combined = final_combined

    def clean_columns(self,df):
        try:
            df = df.copy()

            rename_map = {
                "vendorid": "vendor_id",
                "ratecodeid": "ratecode_id",
                "pulocationid": "pu_location_id",
                "dolocationid": "do_location_id",
            }

            #change col to snake case col is vendorid
            df = df.rename(columns=rename_map)

            #lowercase all columns
            df.columns = df.columns.str.lower()

            #drop columns with Y/N or empty columns
            df = df.drop(columns=["store_and_fwd_flag", "ehail_fee"],errors="ignore")

            logging.info("Succesfully clean columns!")
            logging.info(f"Columns after cleaning: {df.columns.tolist()}")
            return df
        
        except Exception as e:
            logging.error(f"Error cleaning columns, error: {e}")
            raise

    def clean_values(self,df):
        try:                
            # passenger count null fill with 1, passenger is never 0 and there will always be 1 or more passanger
            if "passenger_count" in df.columns:
                df["passenger_count"] = df["passenger_count"].fillna(1)

            # ratecode_id null fill with 99
            if "ratecode_id" in df.columns:
                df["ratecode_id"] = df["ratecode_id"].fillna(99)

            # payment type null fill with 5(unknown)
            if "payment_type" in df.columns:
                df["payment_type"] = df["payment_type"].fillna(5)

            # payment type null fill with 1(streethail)
            if "trip_type" in df.columns:
                df["trip_type"] = df["trip_type"].fillna(1)

            #col end with id, count, type make as int, else pass
            for col in df.columns:
                if col.endswith("_id") or col.endswith("_count") or col.endswith("_type"):
                    df[col] = pd.to_numeric(df[col], errors = "coerce").astype(int)
                else:
                    pass

            # keep valid trips only (drop df with negative values & 0 trip distance)
            df = df[(df["fare_amount"] > 0) & (df["total_amount"] > 0) & (df["trip_distance"] > 0)]
            
            logging.info("Succesfully clean values!")
            return df

        except Exception as e:
            logging.error(f"Error cleaning values, error: {e}")
            raise

    def transform(self):

        transformed_df = {}

        try: 
            for taxi_type, df in self.final_combined.items():
                logging.info(f"Transforming {taxi_type}...")
                df_clean = self.clean_columns(df)
                df_clean = self.clean_values(df_clean)

                transformed_df[taxi_type] = df_clean
                logging.info(f"Transformation successful for {taxi_type} ({len(df_clean):,} rows)")
                
            return transformed_df

        except Exception as e:
            logging.error(f"Error transforming error: {e}")

OUTPUT_DIR = "data/aggregation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Aggregation:
    
    def __init__(self, transformed_data):
        self.transformed_data = transformed_data

    def aggregation_1(self, df):
        # Vendor performance. Group by vendorID, calc mean of fare_amount, sum of trip_distance, count trip
        agg_1 = df.groupby("vendor_id").agg(
            avg_fare=("fare_amount", "mean"),
            total_distance=("trip_distance", "sum"),
            trip_count=("trip_distance", "count")
        ).reset_index()

        return agg_1
    def aggregation_2(self, df):
        #Total revenue per vendorID
        agg_2 = df.groupby("vendor_id").agg(
            fare_amount=("fare_amount", "sum"),
            total_tip=("tip_amount", "sum"),
            total_revenue=("total_amount", "sum")
        ).reset_index()

        return agg_2
    def aggregation_3(self, df):
        #tip stats per vendor
        agg_3 = df.groupby("vendor_id").agg(
            min_tip=("tip_amount", "min"),
            max_tip=("tip_amount", "max"),
            total_tip=("tip_amount", "sum")
        ).reset_index()

        return agg_3
    
    def aggregation_4(self, df):
        #trip count by run_id & vendor_id
        agg_4 = df.groupby(["run_id","vendor_id"])["fare_amount"].count().reset_index(name="trip_count")

        return agg_4
    
    def aggregation_5(self, df):
        #payment distribution 
        agg_5 = df.groupby("payment_type").agg(
            trip_count=("payment_type", "count"),
            avg_fare=("fare_amount", "mean"),
            avg_tip=("tip_amount", "mean"),
            total_revenue=("total_amount", "sum")
        ).reset_index()
        
        # Add percentage
        agg_5["trip_percentage"] = (agg_5["trip_count"] / agg_5["trip_count"].sum() * 100).round(2)
        
        return agg_5

    def aggregations_to_csv(self):
        all_aggregations = {}
        try:
            for taxi_type, df in self.transformed_data.items():
                logging.info(f"Creating csv from {taxi_type} aggregations")

                agg1 = self.aggregation_1(df)
                agg2 = self.aggregation_2(df)
                agg3 = self.aggregation_3(df)
                agg4 = self.aggregation_4(df)
                agg5 = self.aggregation_5(df)

                agg1.to_csv(f"{OUTPUT_DIR}/{taxi_type}_vendor_performance.csv", index=False)
                agg2.to_csv(f"{OUTPUT_DIR}/{taxi_type}_vendor_revenue.csv", index=False)
                agg3.to_csv(f"{OUTPUT_DIR}/{taxi_type}_vendor_tips.csv", index=False)
                agg4.to_csv(f"{OUTPUT_DIR}/{taxi_type}_trips_by_run.csv", index=False)
                agg5.to_csv(f"{OUTPUT_DIR}/{taxi_type}_payment_methods.csv", index=False)

                logging.info(f" {taxi_type} agreggations saved to {OUTPUT_DIR}")
                
                all_aggregations[taxi_type] = {
                    "vendor_performance": agg1,
                    "vendor_revenue": agg2,
                    "vendor_tips": agg3,
                    "trips_by_run": agg4,
                    "payment_methods": agg5
                }

        except Exception as e:
            logging.error(f"CSV not generated due to {e}")

        return all_aggregations
        
