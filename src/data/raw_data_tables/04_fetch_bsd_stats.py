#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_fetch_bsd_stats.py
Testet die BSD Sports API Verbindung
"""

import requests
import os
from dotenv import dotenv_values

# Key aus .env laden
config = dotenv_values(".env")
API_KEY = config["BSD_API_KEY"]

# Test-Request
url = "https://sports.bzzoiro.com/api/leagues/"
headers = {"Authorization": f"Token {API_KEY}"}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
print(response.json())

# Spieler-Stats für Bundesliga abrufen
url_players = "https://sports.bzzoiro.com/api/player-stats/?league=5&season=77333"
headers = {"Authorization": f"Token {API_KEY}"}

response = requests.get(url_players, headers=headers)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Anzahl Spieler: {data.get('count')}")

# Erste Spalten anzeigen
if data.get('results'):
    print("Verfügbare Felder:")
    for key in data['results'][0].keys():
        print(f"  {key}")