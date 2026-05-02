#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_rwi_ratings.py
"""

import pandas as pd
import numpy as np
import os
from math import exp, log
from scipy.stats import poisson

# ══════════════════════════════════════════════════════════════
# KONFIGURATION
# ══════════════════════════════════════════════════════════════
TRAIN_SEASONS = [1516, 1617, 1718, 1819, 1920, 2021, 2122, 2223]
TEST_SEASON   = 2324
K             = 0.02        # Lernrate
HOME_ADV      = 0.1         # Heimvorteil
CLIP          = 1.0         # exp(1.0) ≈ 2.7 max xG
REVERSION     = 0.5         # 50% Mean Reversion zwischen Saisons

INIT = {
    'home_attack':  log(1.5),
    'home_defense': log(1.5),
    'away_attack':  log(1.2),
    'away_defense': log(1.2),
}

DATA_PATH   = "data/processed/bundesliga_history_cleaned.csv"
OUTPUT_DIR  = "data/processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "rwi_ratings.csv")

# ══════════════════════════════════════════════════════════════
# FUNKTIONEN
# ══════════════════════════════════════════════════════════════
def load_data():
    df = pd.read_csv(DATA_PATH)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    print(f"Daten geladen: {len(df)} Spiele")
    return df

def new_team():
    return {k: v for k, v in INIT.items()}

def clip_ratings(ratings):
    for team in ratings:
        for key in ratings[team]:
            ratings[team][key] = max(-CLIP, min(CLIP, ratings[team][key]))
    return ratings

def calc_xg(ratings, home, away):
    h = ratings[home]
    a = ratings[away]
    xg_h = max(-CLIP, min(CLIP, h['home_attack'] + a['away_defense'] + HOME_ADV))
    xg_a = max(-CLIP, min(CLIP, a['away_attack'] + h['home_defense']))
    return exp(xg_h), exp(xg_a)

def calc_probs(xg_home, xg_away, max_goals=8):
    p_home = p_draw = p_away = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson.pmf(h, xg_home) * poisson.pmf(a, xg_away)
            if h > a:   p_home += p
            elif h == a: p_draw += p
            else:        p_away += p
    return p_home, p_draw, p_away

def update(ratings, home, away, actual_h, actual_a, xg_h, xg_a):
    diff_h = actual_h - xg_h
    diff_a = actual_a - xg_a
    ratings[home]['home_attack']  += K * diff_h
    ratings[home]['home_defense'] -= K * diff_a
    ratings[away]['away_attack']  += K * diff_a
    ratings[away]['away_defense'] -= K * diff_h
    return clip_ratings(ratings)

def mean_revert(ratings):
    for team in ratings:
        for key in ratings[team]:
            ratings[team][key] = ratings[team][key] * (1 - REVERSION) + INIT[key] * REVERSION
    return ratings

def train(df, seasons):
    ratings = {}
    print(f"\nTraining auf {len(seasons)} Saisons...")
    
    for season in seasons:
        season_df = df[df['Season'] == season]
        print(f"  Saison {season}: {len(season_df)} Spiele", end="")
        
        for _, match in season_df.iterrows():
            home = match['HomeTeam']
            away = match['AwayTeam']
            if home not in ratings: ratings[home] = new_team()
            if away not in ratings: ratings[away] = new_team()
            
            xg_h, xg_a = calc_xg(ratings, home, away)
            ratings = update(ratings, home, away,
                           int(match['Goals_h']), int(match['Goals_A']),
                           xg_h, xg_a)
        
        # Mean Reversion am Ende jeder Saison
        ratings = mean_revert(ratings)
        print(" ✓")
    
    return ratings

def test(df, season, ratings):
    season_df = df[df['Season'] == season]
    print(f"\nTeste auf Saison {season}: {len(season_df)} Spiele")
    
    results = []
    for _, match in season_df.iterrows():
        home = match['HomeTeam']
        away = match['AwayTeam']
        if home not in ratings: ratings[home] = new_team()
        if away not in ratings: ratings[away] = new_team()
        
        xg_h, xg_a = calc_xg(ratings, home, away)
        p_home, p_draw, p_away = calc_probs(xg_h, xg_a)
        
        probs     = {'H': p_home, 'D': p_draw, 'A': p_away}
        prediction = max(probs, key=probs.get)
        actual     = match['winner']
        
        results.append({
            'Date':       match['Date'],
            'HomeTeam':   home,
            'AwayTeam':   away,
            'xG_Home':    round(xg_h, 2),
            'xG_Away':    round(xg_a, 2),
            'P_Home':     round(p_home, 3),
            'P_Draw':     round(p_draw, 3),
            'P_Away':     round(p_away, 3),
            'Prediction': prediction,
            'Actual':     actual,
            'Correct':    prediction == actual,
        })
    
    return pd.DataFrame(results)

def main():
    df = load_data()
    
    # Training
    ratings = train(df, TRAIN_SEASONS)
    
    # Top Teams anzeigen
    print("\nTop 5 Teams nach Home Attack:")
    top5 = sorted(ratings.items(),
                  key=lambda x: x[1]['home_attack'],
                  reverse=True)[:5]
    for team, r in top5:
        print(f"  {team:20s} home_att={r['home_attack']:.3f} "
              f"away_att={r['away_attack']:.3f} "
              f"home_def={r['home_defense']:.3f}")
    
    # Test
    results = test(df, TEST_SEASON, ratings)
    
    # Ergebnis
    acc = results['Correct'].mean() * 100
    print(f"\n{'='*40}")
    print(f"Genauigkeit: {acc:.1f}%")
    print(f"Korrekt: {results['Correct'].sum()}/{len(results)}")
    print(f"{'='*40}")
    
    print("\nAufschlüsselung:")
    for outcome in ['H', 'D', 'A']:
        sub = results[results['Actual'] == outcome]
        print(f"  {outcome}: {sub['Correct'].mean()*100:.1f}% "
              f"({len(sub)} Spiele)")
    
    print("\nBeispiele:")
    print(results[['HomeTeam','AwayTeam','xG_Home','xG_Away',
                   'Prediction','Actual','Correct']].head(5).to_string())
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results.to_csv(OUTPUT_FILE, index=False)
    print(f"\nGespeichert: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()