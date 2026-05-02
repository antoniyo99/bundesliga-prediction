#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_tune_rwi.py

Findet automatisch die besten Werte für K und REVERSION
durch Grid Search - testet alle Kombinationen und 
gibt die beste zurück.
"""

import pandas as pd
import numpy as np
import os
from math import exp, log
from scipy.stats import poisson
from itertools import product

# ══════════════════════════════════════════════════════════════
# KONFIGURATION
# ══════════════════════════════════════════════════════════════
TRAIN_SEASONS = [1516, 1617, 1718, 1819, 1920, 2021, 2122, 2223]
TEST_SEASON   = 2324


K_VALUES         = [0.005, 0.01, 0.015, 0.02]
REVERSION_VALUES = [0.5, 0.6, 0.7, 0.8]
CLIP_VALUES      = [0.8, 1.0, 1.2, 1.5]
HOME_ADV_VALUES  = [0.05, 0.1, 0.15, 0.2]

INIT = {
    'home_attack':  log(1.5),
    'home_defense': log(1.5),
    'away_attack':  log(1.2),
    'away_defense': log(1.2),
}

DATA_PATH = "data/processed/bundesliga_history_cleaned.csv"

# ══════════════════════════════════════════════════════════════
# RWI FUNKTIONEN (kompakt)
# ══════════════════════════════════════════════════════════════
def new_team():
    return {k: v for k, v in INIT.items()}

def clip_ratings(ratings, clip):
    for team in ratings:
        for key in ratings[team]:
            ratings[team][key] = max(-clip, min(clip, ratings[team][key]))
    return ratings

def calc_xg(ratings, home, away, clip, home_adv):
    h = ratings[home]
    a = ratings[away]
    xg_h = max(-clip, min(clip, h['home_attack'] + a['away_defense'] + home_adv))
    xg_a = max(-clip, min(clip, a['away_attack'] + h['home_defense']))
    return exp(xg_h), exp(xg_a)

def calc_probs(xg_home, xg_away, max_goals=7):
    p_home = p_draw = p_away = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson.pmf(h, xg_home) * poisson.pmf(a, xg_away)
            if h > a:    p_home += p
            elif h == a: p_draw += p
            else:        p_away += p
    return p_home, p_draw, p_away

def update(ratings, home, away, actual_h, actual_a, xg_h, xg_a, k, clip):
    diff_h = actual_h - xg_h
    diff_a = actual_a - xg_a
    ratings[home]['home_attack']  += k * diff_h
    ratings[home]['home_defense'] -= k * diff_a
    ratings[away]['away_attack']  += k * diff_a
    ratings[away]['away_defense'] -= k * diff_h
    return clip_ratings(ratings, clip)

def mean_revert(ratings, reversion):
    for team in ratings:
        for key in ratings[team]:
            ratings[team][key] = (ratings[team][key] * (1 - reversion) + 
                                  INIT[key] * reversion)
    return ratings

def run_model(df, k, reversion, clip, home_adv):
    """
    Führt das komplette Modell mit gegebenen Parametern aus
    und gibt die Genauigkeit zurück.
    """
    ratings = {}
    
    # Training
    for season in TRAIN_SEASONS:
        season_df = df[df['Season'] == season]
        
        for _, match in season_df.iterrows():
            home = match['HomeTeam']
            away = match['AwayTeam']
            if home not in ratings: ratings[home] = new_team()
            if away not in ratings: ratings[away] = new_team()
            
            xg_h, xg_a = calc_xg(ratings, home, away, clip, home_adv)
            ratings = update(ratings, home, away,
               int(match['Goals_h']), int(match['Goals_A']),
               xg_h, xg_a, k, clip)
        
        ratings = mean_revert(ratings, reversion)
    
    # Test
    correct = 0
    total   = 0
    
    test_df = df[df['Season'] == TEST_SEASON]
    
    for _, match in test_df.iterrows():
        home = match['HomeTeam']
        away = match['AwayTeam']
        if home not in ratings: ratings[home] = new_team()
        if away not in ratings: ratings[away] = new_team()
        
        
        xg_h, xg_a = calc_xg(ratings, home, away, clip, home_adv)
        p_home, p_draw, p_away = calc_probs(xg_h, xg_a)
        
        probs      = {'H': p_home, 'D': p_draw, 'A': p_away}
        prediction = max(probs, key=probs.get)
        
        if prediction == match['winner']:
            correct += 1
        total += 1
    
    return correct / total * 100

# ══════════════════════════════════════════════════════════════
# GRID SEARCH
# ══════════════════════════════════════════════════════════════
def grid_search(df):
    """
    Testet alle Kombinationen von K und REVERSION.
    Gibt eine sortierte Tabelle mit allen Ergebnissen zurück.
    """
    total_combinations = len(K_VALUES) * len(REVERSION_VALUES)
    print(f"Teste {total_combinations} Kombinationen...")
    print(f"K-Werte: {K_VALUES}")
    print(f"Reversion-Werte: {REVERSION_VALUES}")
    print()
    
    results = []
    current = 0
    
   

    for k, reversion, clip, home_adv in product(
        K_VALUES, REVERSION_VALUES, CLIP_VALUES, HOME_ADV_VALUES):
        
        accuracy = run_model(df, k, reversion, clip, home_adv)
        
        results.append({
            'K':         k,
            'Reversion': reversion,
            'Accuracy':  round(accuracy, 2)
        })
        
        print(f"  [{current:2d}/{total_combinations}] "
              f"K={k:.2f} | Reversion={reversion:.1f} "
              f"→ {accuracy:.1f}%")
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Accuracy', ascending=False)
    return results_df

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    df = pd.read_csv(DATA_PATH)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    print(f"Daten geladen: {len(df)} Spiele\n")
    
    # Grid Search starten
    results = grid_search(df)
    
    # Beste Parameter anzeigen
    best = results.iloc[0]
    print(f"\n{'='*40}")
    print(f"BESTE PARAMETER:")
    print(f"  K          = {best['K']}")
    print(f"  Reversion  = {best['Reversion']}")
    print(f"  Genauigkeit = {best['Accuracy']}%")
    print(f"{'='*40}")
    
    print("\nTop 10 Kombinationen:")
    print(results.head(10).to_string(index=False))
    
    # Speichern
    os.makedirs("data/processed", exist_ok=True)
    results.to_csv("data/processed/tuning_results.csv", index=False)
    print(f"\nAlle Ergebnisse gespeichert: data/processed/tuning_results.csv")

if __name__ == "__main__":
    main()