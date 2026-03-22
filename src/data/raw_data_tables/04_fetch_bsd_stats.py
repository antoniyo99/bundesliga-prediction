#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_fetch_bsd_stats.py
Lädt detaillierte Spieler-Stats von BSD Sports API
für alle verfügbaren Bundesliga-Saisons.
"""

import requests
import pandas as pd
import os
import time
from dotenv import dotenv_values

# ── Konfiguration ──────────────────────────────────────────────────────────────
config = dotenv_values(".env")
API_KEY = config["BSD_API_KEY"]
BASE_URL = "https://sports.bzzoiro.com/api"
BUNDESLIGA_ID = 5
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "bsd_player_stats.csv")
# ──────────────────────────────────────────────────────────────────────────────

def get_headers():
    return {"Authorization": f"Token {API_KEY}"}

def get_all_seasons():
    url = f"{BASE_URL}/seasons/?league={BUNDESLIGA_ID}"
    response = requests.get(url, headers=get_headers())
    print(f"Status: {response.status_code}")
    print(f"Antwort: {response.text[:500]}")
    return []

def get_player_stats_for_season(season_id: int, season_name: str) -> pd.DataFrame:
    """
    Holt alle Spieler-Stats für eine Saison.
    Die API gibt Daten seitenweise zurück (Pagination) –
    wir laden alle Seiten bis keine mehr übrig sind.
    """
    all_results = []
    url = f"{BASE_URL}/player-stats/?league={BUNDESLIGA_ID}&season={season_id}"
    page = 1
    
    while url:
        print(f"  Seite {page}...", end=" ")
        response = requests.get(url, headers=get_headers())
        
        if response.status_code != 200:
            print(f"Fehler: {response.status_code}")
            break
            
        data = response.json()
        results = data.get("results", [])
        all_results.extend(results)
        
        url = data.get("next")  # Nächste Seite oder None
        page += 1
        
        time.sleep(0.5)  # Server schonen
    
    print(f"→ {len(all_results)} Einträge")
    
    if not all_results:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_results)
    df["season_name"] = season_name
    return df

def map_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Mappt BSD-Spalten auf unser Schema."""
    
    # Pass Accuracy berechnen (accurate / total * 100)
    df["Pass_Accuracy"] = (
        pd.to_numeric(df["accurate_pass"], errors="coerce") /
        pd.to_numeric(df["total_pass"], errors="coerce") * 100
    ).round(1)
    
    # Save % berechnen (saves / (saves + goals_conceded) * 100)
    saves = pd.to_numeric(df["saves"], errors="coerce").fillna(0)
    conceded = pd.to_numeric(df["goals_conceded"], errors="coerce").fillna(0)
    df["Save_Pct"] = (saves / (saves + conceded) * 100).round(1)
    
    # Spalten umbenennen
    column_map = {
        "minutes_played":   "Minutes_Played",
        "goals":            "Goals",
        "goal_assist":      "Assists",
        "expected_goals":   "xG",
        "expected_assists": "xA",
        "shots_on_target":  "Shots_on_Target",
        "key_pass":         "Key_Passes",
        "total_tackle":     "Tackles_Total",
        "won_tackle":       "DTackles_Won",
        "interception":     "Interceptions",
        "aerial_won":       "Aerial_Won",
        "aerial_lost":      "Aerial_Lost",
        "ball_recovery":    "Ball_Recoveries",
        "touches":          "Touches_Control",
        "dispossessed":     "Dispossessed",
        "yellow_card":      "Cards_Y",
        "red_card":         "Cards_R",
        "saves":            "GK_Saves",
        "goals_conceded":   "Goals_Allowed",
        "total_clearance":  "Clearances",
        "fouls":            "Fouls",
        "was_fouled":       "Fouled",
        "rating":           "Rating",
        "season_name":      "Season",
        "event":            "Match_ID",
    }
    
    df = df.rename(columns=column_map)
    
    # Nur relevante Spalten behalten
    keep_cols = [c for c in column_map.values() if c in df.columns]
    keep_cols += ["Pass_Accuracy", "Save_Pct"]
    df = df[keep_cols]
    
    # Alle numerischen Spalten konvertieren
    skip_cols = ["Season", "Match_ID"]
    for col in df.columns:
        if col not in skip_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Saisons laden
    seasons = get_all_seasons()
    
    if not seasons:
        print("Keine Saisons gefunden!")
        return
    
    all_data = []
    
    for season in seasons:
        season_id = season.get("id")
        season_name = season.get("name", str(season_id))
        
        print(f"\nLade Saison: {season_name}...")
        df = get_player_stats_for_season(season_id, season_name)
        
        if not df.empty:
            all_data.append(df)
    
    if not all_data:
        print("Keine Daten geladen!")
        return
    
    # Alles zusammenführen
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Schema mappen
    final_df = map_to_schema(final_df)
    
    # Speichern
    final_df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "="*40)
    print("FERTIG!")
    print(f"Gespeichert: {OUTPUT_FILE}")
    print(f"Gesamte Zeilen: {len(final_df)}")
    print(f"Spalten: {list(final_df.columns)}")
    print("="*40)
    print("\nBeispiel:")
    print(final_df[["Season", "Goals", "Assists", 
                     "DTackles_Won", "Pass_Accuracy"]].head(3))

if __name__ == "__main__":
    main()