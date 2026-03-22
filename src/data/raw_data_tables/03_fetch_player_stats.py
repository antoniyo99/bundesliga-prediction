#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_fetch_player_stats.py
Lädt Spieler-Stats von Understat für alle Bundesliga-Saisons
und speichert sie im master_player_stats.csv Format.
"""

import asyncio
import aiohttp
import understat
import pandas as pd
import os

# ── Konfiguration ──────────────────────────────────────────────────────────────
SEASONS = list(range(2014, 2025))   # 2014/15 bis 2024/25
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "master_player_stats.csv")
# ──────────────────────────────────────────────────────────────────────────────

async def fetch_all_seasons(seasons: list) -> pd.DataFrame:
    """
    Holt alle Saisons in einer einzigen Session –
    das ist schneller und schonender für den Server.
    """
    all_data = []
    
    async with aiohttp.ClientSession() as session:
        api = understat.Understat(session)
        
        for season in seasons:
            try:
                print(f"Lade Saison {season}/{season+1}...")
                players = await api.get_league_players("Bundesliga", season)
                
                df = pd.DataFrame(players)
                df["Season"] = f"{season}/{season+1}"
                all_data.append(df)
                
                print(f"  {len(players)} Spieler geladen.")
                
                # Kurz warten damit der Server nicht überlastet wird
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  Fehler bei Saison {season}: {e} – wird übersprungen.")
    
    return pd.concat(all_data, ignore_index=True)


def map_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Übersetzt Understat-Spalten in unser Schema
    und bereinigt die Positionen.
    """
    # Spalten umbenennen
    column_map = {
        "player_name":  "Player_Name",
        "team_title":   "Team",
        "position":     "Position_Played",
        "time":         "Minutes_Played",
        "goals":        "Goals",
        "assists":      "Assists",
        "shots":        "Shots_on_Target",
        "key_passes":   "Key_Passes",
        "yellow_cards": "Cards_Y",
        "red_cards":    "Cards_R",
        "xG":           "xG",
        "xA":           "xA",
        "xGChain":      "xGChain",
        "xGBuildup":    "xGBuildup",
        "npg":          "Non_Penalty_Goals",
        "npxG":         "npxG",
        "games":        "Games_Played",
    }
    df = df.rename(columns=column_map)
    
    # Position bereinigen – alle möglichen Understat-Codes abdecken
    
    
   
    
    def clean_position(pos):
        pos = str(pos).strip().upper()
        # S = Substitute rausfiltern, spielt keine Rolle für Position
        pos = pos.replace(" S", "").strip()
        
        if "GK" in pos:
            return "GK"
        elif pos == "D" or pos == "D M":
            return "DF"
        elif "F" in pos or pos == "S":
            return "FW"
        elif "M" in pos:
            return "MF"
        elif pos == "D F M":
            return "MF"  # Vielseitig, Mittelfeld als Default
        else:
            return "MF"

    df["Position_Played"] = df["Position_Played"].apply(clean_position)


    # Numerische Spalten konvertieren
    numeric_cols = [
        "Minutes_Played", "Goals", "Assists", "Shots_on_Target",
        "Key_Passes", "Cards_Y", "Cards_R", "xG", "xA",
        "xGChain", "xGBuildup", "Non_Penalty_Goals", "npxG", "Games_Played"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Nur relevante Spalten behalten
    keep_cols = [
        "Player_Name", "Team", "Season", "Position_Played",
        "Minutes_Played", "Games_Played",
        "Goals", "Assists", "Shots_on_Target", "Key_Passes",
        "Cards_Y", "Cards_R",
        "xG", "xA", "xGChain", "xGBuildup",
        "Non_Penalty_Goals", "npxG"
    ]
    df = df[[c for c in keep_cols if c in df.columns]]
    
    return df


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Starte Download für alle Saisons...")
    print(f"Saisons: {SEASONS[0]}/{SEASONS[0]+1} bis {SEASONS[-1]}/{SEASONS[-1]+1}")
    print("="*40)
    
    # Alle Saisons laden
    raw_df = asyncio.run(fetch_all_seasons(SEASONS))
    
    # Schema mappen
    df = map_to_schema(raw_df)
    
    # Speichern
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "="*40)
    print("FERTIG!")
    print(f"Gespeichert: {OUTPUT_FILE}")
    print(f"Gesamte Zeilen: {len(df)}")
    print(f"Saisons: {df['Season'].unique()}")
    print("="*40)
    print("\nBeispiel Daten:")
    print(df[["Player_Name", "Team", "Season", 
              "Position_Played", "Goals", "xG"]].head(5))


if __name__ == "__main__":
    main()