#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 16:27:23 2026

@author: antoniosimunovic
"""

import os
import pandas as pd

# 1. Define Paths
project_root = "/Users/antoniosimunovic/bundesliga-prediction"
bronze_path = os.path.join(project_root, "data", "raw", "master_player_stats.csv")
silver_dir = os.path.join(project_root, "data", "processed")

# 2. Create the processed folder if it doesn't exist
os.makedirs(silver_dir, exist_ok=True)

# 3. Load the Master Bronze Data
# (Note: For now it's empty, but this script is built to handle data once scraped)
try:
    master_df = pd.read_csv(bronze_path)
except FileNotFoundError:
    print("Error: Master Bronze file not found. Run script 01 first.")
    master_df = pd.DataFrame() # Fallback

# 4. Define Column Logic for each Silver Table
# These are the variables we'll actually use for Elo math
silver_schemas = {
    'GK': ['Match_ID', 'Player_Name', 'Team', 'GK_Save_Pct', 'GK_Goals_Prevented', 'GK_Goals_Allowed', 'Pen_Errors'],
    'DF': ['Match_ID', 'Player_Name', 'Team', 'Def_Clean_Sheet', 'Def_Interceptions', 'Def_Tackles_Won', 'Def_Blocks', 'Def_Aerial_Won', 'Def_Dribbled_Past', 'Pen_Errors'],
    'MF': ['Match_ID', 'Player_Name', 'Team', 'Mid_Pass_Accuracy', 'Mid_Key_Passes', 'Mid_Touches_Control', 'Mid_Ball_Recoveries', 'Mid_Distance_Covered', 'Pen_Dispossessed'],
    'FW': ['Match_ID', 'Player_Name', 'Team', 'Att_Goals', 'Att_Assists', 'Att_Shots_on_Target', 'Att_Big_Chances_Missed', 'Pen_Dispossessed']
}

# 5. Create and Save the 4 Silver Tables
for pos, cols in silver_schemas.items():
    # Filter master data by position and select specific columns
    pos_df = master_df[master_df['Position_Played'] == pos][cols]
    
    # Define save path
    save_path = os.path.join(silver_dir, f"silver_players_{pos.lower()}.csv")
    
    # Save (even if empty for now, it creates the headers)
    pos_df.to_csv(save_path, index=False)
    print(f"Created Silver Table: {save_path}")

print("\nAll 4 Silver Position Tables are ready in /data/processed/")