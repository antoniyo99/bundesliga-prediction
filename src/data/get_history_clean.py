import pandas as pd
import os
import time

def download_bundesliga_history():
    """
    Downloads historical Bundesliga data from football-data.co.uk 
    for the last 10 seasons and saves it as a CSV.
    """
    all_seasons_data = []
    
    # Season strings used in the URL (e.g., '2324' for 2023/24)
    seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425"]
    
    # Base URL for the German Bundesliga (D1)
    base_url = "https://www.football-data.co.uk/mmz4281/{}/D1.csv"
    
    for season_code in seasons:
        print(f"Downloading data for season {season_code}...")
        
        # Insert the season_code into the URL
        url = base_url.format(season_code)
        
        try:
            # pd.read_csv can fetch data directly from a web URL
            df_season = pd.read_csv(url)
            
            # Add a column to keep track of which season the data belongs to
            df_season['Season'] = season_code
            
            all_seasons_data.append(df_season)
            print(f"Success: Loaded {len(df_season)} matches.")
            
        except Exception as e:
            print(f"Failed to download season {season_code}: {e}")
        
        # Respect the server by waiting 1 second between requests
        time.sleep(1)

    # If we successfully collected data, combine it all into one table
    if all_seasons_data:
        # pd.concat stacks the individual DataFrames on top of each other
        final_df = pd.concat(all_seasons_data, ignore_index=True)
        
        # Define the output path
        output_dir = 'data/raw'
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, 'bundesliga_history_free.csv')
        
        # Save the master dataset
        final_df.to_csv(file_path, index=False)
        
        print("\n" + "="*30)
        print("DOWNLOAD COMPLETE")
        print(f"Total matches collected: {len(final_df)}")
        print(f"File saved at: {file_path}")
        print("="*30)
    else:
        print("No data was collected.")

if __name__ == "__main__":
    download_bundesliga_history()
    
    
    
    

def preprocess_raw_data():
# 1. Load the raw data we just downloaded
    input_path = 'data/raw/bundesliga_history_free.csv'

    if not os.path.exists(input_path):
        print("Error: Raw file not found!")
        return
    
    df = pd.read_csv(input_path)
    
    # 2. Define the Mapping (Old Name : New Name)
    # This aligns the CSV columns with your preferred names
    column_mapping = {
        'Date': 'Date',
        'HomeTeam': 'HomeTeam',
        'AwayTeam': 'AwayTeam',
        'FTHG': 'Goals_h',      # Full Time Home Goals
        'FTAG': 'Goals_A',      # Full Time Away Goals
        'HTHG': 'Goals_H_ht',   # Half Time Home Goals
        'HTAG': 'Goals_A_ht',   # Half Time Away Goals
        'FTR': 'winner',        # Full Time Result (H, D, A)
        'Season': 'Season'
    }
    
    # 3. Filter and Rename
    # We only keep the columns we defined in the mapping
    df_cleaned = df[column_mapping.keys()].rename(columns=column_mapping)
    
    # 4. Data Cleaning: Convert Date
    # The dates in the CSV are strings; we convert them to actual Python datetime objects
    df_cleaned['Date'] = pd.to_datetime(df_cleaned['Date'], dayfirst=True)
    
    # 5. Save the processed data
    output_dir = 'data/processed'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'bundesliga_history_cleaned.csv')
    
    df_cleaned.to_csv(output_path, index=False)
    
    print(f"Success! Cleaned data saved to: {output_path}")
    print(df_cleaned.head()) # Shows the first 5 rows of the new table

if __name__ == "__main__":
    preprocess_raw_data()
    
    
    
    
    
    
    
    