#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 16:07:26 2026

@author: antoniosimunovic
"""

import pandas as pd
import os

# 1. Define the complete list of columns for all player types
columns = [
    # Metadata & Identifiers
    'Match_ID', 'Date', 'Player_ID', 'Player_Name', 'Team', 'Opponent', 
    'Position_Played', 'Minutes_Played',
    
    # Goalkeeping (Raw)
    'Save_Pct', 'Goals_Prevented', 'Goals_Allowed', 'Bad_Long_Balls',
    
    # Defending (Raw)
    'Clean_Sheet', 'Interceptions', 'DTackles_Won', 'Blocks', 'Aerial_Won', 
    'Dribbled_Past',
    
    # Midfield & Physical (Raw)
    'Pass_Accuracy', 'Key_Passes', 'Touches_Control', 'Ball_Recoveries', 
    'Distance_Covered',
    
    # Attacking (Raw)
    'Goals', 'Assists', 'Shots_on_Target', 'Dribble_Success', 
    'Big_Chances_Missed',
    
    # Penalties & Discipline (Universal)
    'Dispossessed', 'Miscontrols', 'Errors', 'Cards_Y', 'Cards_R'
]

# 2. Initialize the Empty DataFrame
master_player_df = pd.DataFrame(columns=columns)
# 1. Define your PROJECT root path explicitly
# Replace this with the actual path to your main project folder
project_root = "/Users/antoniosimunovic/bundesliga-prediction"

# 2. Define the path to data_raw
data_raw_folder = os.path.join(project_root, "data", "raw")
file_path = os.path.join(data_raw_folder, "master_player_stats.csv")

# 3. Create folder if missing and save
os.makedirs(data_raw_folder, exist_ok=True)
master_player_df.to_csv(file_path, index=False)

print(f"DONE! File is now at: {file_path}")