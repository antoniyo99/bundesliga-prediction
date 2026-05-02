#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_fetch_fbref_match_stats.py

Lädt Spieler-Stats pro Spiel von FBref für die Bundesliga.
Nutzt Camoufox um Cloudflare zu umgehen.

Output:
    data/raw/fbref_match_player_stats.csv
"""

import asyncio
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
from camoufox.async_api import AsyncCamoufox
import os
import time

# ══════════════════════════════════════════════════════════════
# KONFIGURATION
# ══════════════════════════════════════════════════════════════
SEASONS = {
    "2023-2024": "https://fbref.com/en/comps/20/2023-2024/schedule/2023-2024-Bundesliga-Scores-and-Fixtures",
    "2024-2025": "https://fbref.com/en/comps/20/2024-2025/schedule/2024-2025-Bundesliga-Scores-and-Fixtures",
}

OUTPUT_DIR  = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "fbref_match_player_stats.csv")

# Pause zwischen Requests (Sekunden) – wichtig um nicht geblockt zu werden
PAUSE = 8

# ══════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ══════════════════════════════════════════════════════════════
def get_match_links(soup, season):
    """Extrahiert alle eindeutigen Match-Links aus der Spielplan-Seite."""
    links = list(set([
        'https://fbref.com' + a['href']
        for a in soup.find_all('a', href=True)
        if '/matches/' in a['href'] and 'Bundesliga' in a['href']
    ]))
    print(f"  {len(links)} Spiele gefunden")
    return links

def parse_player_table(table, team, match_id, date, season):
    """
    Bereinigt eine Spieler-Stats Tabelle und fügt Metadaten hinzu.
    """
    try:
        # Multi-Index bereinigen falls vorhanden
        if isinstance(table.columns, pd.MultiIndex):
            table.columns = table.columns.droplevel(0)
        
        # Nur relevante Spalten behalten
        keep = ['Player', 'Pos', 'Min', 'Gls', 'Ast', 
                'Sh', 'SoT', 'CrdY', 'CrdR', 
                'TklW', 'Int', 'Fls', 'Fld']
        existing = [c for c in keep if c in table.columns]
        df = table[existing].copy()
        
        # Metadaten hinzufügen
        df['Team']     = team
        df['Match_ID'] = match_id
        df['Date']     = date
        df['Season']   = season
        
        # Letzte Zeile (Summe) entfernen
        df = df[df['Player'].notna()]
        df = df[df['Player'] != 'Players']
        
        return df
    except Exception as e:
        print(f"    Fehler beim Parsen: {e}")
        return pd.DataFrame()

def extract_teams_from_title(title):
    """Extrahiert Heim- und Auswärtsteam aus dem Seitentitel."""
    try:
        # Format: "Team A vs. Team B Match Report – ..."
        parts = title.split(' Match Report')[0]
        teams = parts.split(' vs. ')
        return teams[0].strip(), teams[1].strip()
    except:
        return "Unknown", "Unknown"

def extract_match_id(url):
    """Extrahiert die Match-ID aus der URL."""
    return url.split('/matches/')[1].split('/')[0]

# ══════════════════════════════════════════════════════════════
# HAUPT-SCRAPING FUNKTION
# ══════════════════════════════════════════════════════════════
async def scrape_season(page, season_name, schedule_url):
    """
    Scrapt alle Spiele einer Saison.
    """
    print(f"\nLade Spielplan für {season_name}...")
    await page.goto(schedule_url)
    await page.wait_for_timeout(8000)
    
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')
    links = get_match_links(soup, season_name)
    
    all_players = []
    total = len(links)
    
    for i, url in enumerate(links):
        print(f"  [{i+1}/{total}] {url.split('/')[-1][:50]}...", end=" ")
        
        try:
            await page.goto(url)
            await page.wait_for_timeout(PAUSE * 1000)
            
            title = await page.title()
            
            # Überprüfen ob Seite geladen
            if 'Just a moment' in title or 'Sicherheit' in title:
                print("⚠ Cloudflare – warte länger...")
                await page.wait_for_timeout(10000)
                title = await page.title()
            
            content = await page.content()
            tables = pd.read_html(StringIO(content))
            
            home_team, away_team = extract_teams_from_title(title)
            match_id = extract_match_id(url)
            
            # Datum aus URL extrahieren
            date = url.split('-')[-4] + '-' + url.split('-')[-3] + '-' + url.split('-')[-2]
            
            # Spieler-Tabellen finden (Tabellen mit 'Player' Spalte und 15+ Zeilen)
            player_tables = []
            for t in tables:
                cols = t.columns
                if isinstance(cols, pd.MultiIndex):
                    cols = cols.droplevel(0)
                if 'Player' in cols and len(t) > 5:
                    player_tables.append(t)
            
            if len(player_tables) >= 2:
                # Heimteam (erste Tabelle)
                home_df = parse_player_table(
                    player_tables[0], home_team, match_id, date, season_name)
                # Auswärtsteam (zweite Tabelle)
                away_df = parse_player_table(
                    player_tables[1], away_team, match_id, date, season_name)
                
                all_players.append(home_df)
                all_players.append(away_df)
                
                print(f"✓ ({len(home_df)+len(away_df)} Spieler)")
            else:
                print(f"⚠ Keine Spieler-Tabellen gefunden")
                
        except Exception as e:
            print(f"✗ Fehler: {e}")
        
        # Fortschritt zwischenspeichern alle 10 Spiele
        if (i + 1) % 10 == 0 and all_players:
            temp_df = pd.concat(all_players, ignore_index=True)
            temp_df.to_csv(OUTPUT_FILE.replace('.csv', '_temp.csv'), index=False)
            print(f"  → Zwischenstand gespeichert: {len(temp_df)} Einträge")
    
    return all_players

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_data = []
    
    async with AsyncCamoufox(headless=False) as browser:
        page = await browser.new_page()
        
        for season_name, schedule_url in SEASONS.items():
            season_data = await scrape_season(page, season_name, schedule_url)
            all_data.extend(season_data)
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(OUTPUT_FILE, index=False)
        
        print(f"\n{'='*40}")
        print(f"FERTIG!")
        print(f"Gespeichert: {OUTPUT_FILE}")
        print(f"Gesamte Einträge: {len(final_df)}")
        print(f"Saisons: {final_df['Season'].unique()}")
        print(f"{'='*40}")
        print(final_df.head(3))

if __name__ == "__main__":
    asyncio.run(main())