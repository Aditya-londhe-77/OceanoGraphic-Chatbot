import os
import pandas as pd
import xarray as xr
from sqlalchemy import create_engine

DB_CONNECTION_STRING = "postgresql://postgres.nshbsuintqovdbqpcnyc:Aditya.in.77@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

TEMP_CSV_DIR = 'TempCsvData'
CLEAN_DATA_DIR = 'CleanData'

NC_FILES_TO_PROCESS = {
    '6902746_tech.nc': 'TechnicalData.csv',
    '6902746_meta.nc': 'MetaData.csv',
    '6902746_traj.nc': 'RealtimeTrajData.csv'
}

def convert_nc_to_csv(nc_file_path, csv_output_path):
    try:
        print(f"  Converting '{nc_file_path}' to CSV...")
        ds = xr.open_dataset(nc_file_path)
        df = ds.to_dataframe().reset_index()
        df.to_csv(csv_output_path, index=False)
        print(f"  Successfully saved to '{csv_output_path}'")
        return True
    except FileNotFoundError:
        print(f"  ERROR: NetCDF file not found at '{nc_file_path}'")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred during NC to CSV conversion: {e}")
        return False

def clean_generic_data(input_path, output_path):
    try:
        print(f"  Cleaning '{input_path}'...")
        df = pd.read_csv(input_path)
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].astype(str).str.contains("b'").any():
                df[col] = df[col].str.strip("b'").str.strip()
        
        df.to_csv(output_path, index=False)
        print(f"  Successfully saved cleaned data to '{output_path}'")
        return True
    except FileNotFoundError:
        print(f"  ERROR: File not found at '{input_path}'.")
        return False
    except Exception as e:
        print(f"  An error occurred while cleaning '{input_path}': {e}")
        return False

def process_trajectory_data(input_path, traj_output_path, profile_output_path):
    try:
        print(f"  Processing trajectory data from '{input_path}'...")
        traj_df = pd.read_csv(input_path)

        trajectory_data = traj_df.dropna(subset=['LATITUDE', 'LONGITUDE'])
        trajectory_data = trajectory_data[['N_MEASUREMENT', 'LATITUDE', 'LONGITUDE']]
        trajectory_data.to_csv(traj_output_path, index=False)
        print(f"  Successfully saved trajectory data to '{traj_output_path}'")

        profile_data = traj_df.dropna(subset=['PRES', 'TEMP', 'PSAL'])
        profile_data = profile_data[['N_MEASUREMENT', 'PRES', 'TEMP', 'PSAL']]
        profile_data.to_csv(profile_output_path, index=False)
        print(f"  Successfully saved profile data to '{profile_output_path}'")

        return True
    except FileNotFoundError:
        print(f"  ERROR: File not found at '{input_path}'.")
        return False
    except Exception as e:
        print(f"  An error occurred while processing trajectory data: {e}")
        return False

def load_csv_to_db(file_path, table_name, engine):
    try:
        print(f"  Loading '{file_path}' into table '{table_name}'...")
        df = pd.read_csv(file_path)
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"  Successfully loaded data into '{table_name}'.")
        return True
    except FileNotFoundError:
        print(f"  ERROR: The file '{file_path}' was not found.")
        return False
    except Exception as e:
        print(f"  An error occurred while loading data into '{table_name}': {e}")
        return False

if __name__ == "__main__":
    print("--- Starting Full Data Pipeline ---")

    os.makedirs(TEMP_CSV_DIR, exist_ok=True)
    os.makedirs(CLEAN_DATA_DIR, exist_ok=True)
    
    pipeline_successful = True

    print("\n[STAGE 1/3] Converting NetCDF files to CSV...")
    for nc_file, csv_name in NC_FILES_TO_PROCESS.items():
        if not convert_nc_to_csv(nc_file, os.path.join(TEMP_CSV_DIR, csv_name)):
            pipeline_successful = False
            break
    
    if pipeline_successful:
        print("\n[STAGE 2/3] Cleaning and processing data...")
        tech_cleaned = clean_generic_data(
            os.path.join(TEMP_CSV_DIR, 'TechnicalData.csv'),
            os.path.join(CLEAN_DATA_DIR, 'technical_cleaned.csv')
        )
        meta_cleaned = clean_generic_data(
            os.path.join(TEMP_CSV_DIR, 'MetaData.csv'),
            os.path.join(CLEAN_DATA_DIR, 'metadata_cleaned.csv')
        )
        traj_processed = process_trajectory_data(
            os.path.join(TEMP_CSV_DIR, 'RealtimeTrajData.csv'),
            os.path.join(CLEAN_DATA_DIR, 'trajectory_processed.csv'),
            os.path.join(CLEAN_DATA_DIR, 'profiles_processed.csv')
        )
        if not (tech_cleaned and meta_cleaned and traj_processed):
            pipeline_successful = False

    if pipeline_successful:
        print("\n[STAGE 3/3] Loading data into PostgreSQL database...")
        try:
            engine = create_engine(DB_CONNECTION_STRING)
            
            datasets_to_load = {
                os.path.join(CLEAN_DATA_DIR, 'metadata_cleaned.csv'): 'argo_metadata',
                os.path.join(CLEAN_DATA_DIR, 'profiles_processed.csv'): 'argo_profiles',
                os.path.join(CLEAN_DATA_DIR, 'trajectory_processed.csv'): 'argo_trajectory',
                os.path.join(CLEAN_DATA_DIR, 'technical_cleaned.csv'): 'argo_technical'
            }
            
            for file_path, table_name in datasets_to_load.items():
                if not load_csv_to_db(file_path, table_name, engine):
                    pipeline_successful = False
                    break
        except Exception as e:
            print(f"\nFATAL ERROR: Failed to connect to the database.")
            print(f"Error details: {e}")
            pipeline_successful = False

    print("-" * 40)
    if pipeline_successful:
        print("\nData processing pipeline completed successfully!")
    else:
        print("\nData processing pipeline encountered errors. Please check the logs above.")
    print("-" * 40)