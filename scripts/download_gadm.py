#!/usr/bin/env python3
"""
Script pour télécharger et simplifier les données GADM pour Mawaquit Web
"""

import geopandas as gpd
import json
import os
import sys
from pathlib import Path

# Liste des pays avec leurs codes ISO
COUNTRIES = [
    ("Algeria", "DZA"),
    ("Argentina", "ARG"),
    ("Austria", "AUT"),
    ("Belgium", "BEL"),
    ("Brazil", "BRA"),
    ("Canada", "CAN"),
    ("Denmark", "DNK"),
    ("Egypt", "EGY"),
    ("France", "FRA"),
    ("Germany", "DEU"),
    ("Greece", "GRC"),
    ("India", "IND"),
    ("Indonesia", "IDN"),
    ("Italy", "ITA"),
    ("Kuwait", "KWT"),
    ("Mexico", "MEX"),
    ("Morocco", "MAR"),
    ("Netherlands", "NLD"),
    ("Norway", "NOR"),
    ("Pakistan", "PAK"),
    ("Poland", "POL"),
    ("Portugal", "PRT"),
    ("Qatar", "QAT"),
    ("Saudi Arabia", "SAU"),
    ("South Africa", "ZAF"),
    ("Spain", "ESP"),
    ("Sweden", "SWE"),
    ("Switzerland", "CHE"),
    ("Tunisia", "TUN"),
    ("Turkey", "TUR"),
    ("UAE", "ARE"),
    ("United Kingdom", "GBR"),
    ("United States", "USA"),
]

GADM_BASE_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json"
OUTPUT_DIR = Path(__file__).parent.parent / "web" / "data" / "gadm"

# Tolérance de simplification (en degrés)
# 0.01 degré ≈ 1 km à l'équateur
SIMPLIFY_TOLERANCE = 0.01


def download_and_simplify(country_name, country_code, level):
    """Télécharge et simplifie les données GADM pour un pays"""
    url = f"{GADM_BASE_URL}/gadm41_{country_code}_{level}.json"
    output_file = OUTPUT_DIR / f"{country_code}_{level}.json"

    # Skip if already exists
    if output_file.exists():
        print(f"  ✓ {country_code} level {level} already exists, skipping")
        return True

    try:
        print(f"  Downloading {country_code} level {level}...", end=" ", flush=True)
        gdf = gpd.read_file(url)

        # Simplifier les géométries
        gdf['geometry'] = gdf['geometry'].simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)

        # Convertir en GeoJSON
        geojson = json.loads(gdf.to_json())

        # Réduire la précision des coordonnées (4 décimales ≈ 11m)
        def round_coords(coords):
            if isinstance(coords[0], (int, float)):
                return [round(c, 4) for c in coords]
            return [round_coords(c) for c in coords]

        for feature in geojson['features']:
            if feature['geometry'] and feature['geometry']['coordinates']:
                feature['geometry']['coordinates'] = round_coords(feature['geometry']['coordinates'])
            # Garder uniquement les propriétés essentielles
            props = feature['properties']
            essential = {}
            for key in ['GID_0', 'COUNTRY', 'NAME_1', 'GID_1']:
                if key in props:
                    essential[key] = props[key]
            feature['properties'] = essential

        # Sauvegarder
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, separators=(',', ':'))  # Compact JSON

        # Afficher la taille
        size_kb = output_file.stat().st_size / 1024
        print(f"OK ({size_kb:.1f} KB)")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        return False


def main():
    print("=" * 60)
    print("Téléchargement et simplification des données GADM")
    print("=" * 60)

    # Créer le répertoire de sortie
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(COUNTRIES)
    success = 0
    failed = []

    for i, (name, code) in enumerate(COUNTRIES, 1):
        print(f"\n[{i}/{total}] {name} ({code})")

        # Niveau 0 (frontières nationales)
        if download_and_simplify(name, code, 0):
            success += 1
        else:
            failed.append(f"{code}_0")

        # Niveau 1 (régions/provinces)
        if not download_and_simplify(name, code, 1):
            failed.append(f"{code}_1")

    print("\n" + "=" * 60)
    print(f"Terminé: {success}/{total} pays téléchargés")

    if failed:
        print(f"Échecs: {', '.join(failed)}")

    # Calculer la taille totale
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.glob("*.json"))
    print(f"Taille totale: {total_size / (1024*1024):.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
