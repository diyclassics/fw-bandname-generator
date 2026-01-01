#!/usr/bin/env python3
"""
Wikidata Band Names Automation Script

Fetches band names from Wikidata's SPARQL endpoint and updates static/data/bands.txt
"""

import requests
import time


WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# SPARQL query to fetch musical groups/bands (Q215380)
SPARQL_QUERY = """
SELECT DISTINCT ?item ?itemLabel WHERE {
  ?item wdt:P31/wdt:P279* wd:Q215380 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""


def fetch_bands_from_wikidata():
    """
    Query Wikidata SPARQL endpoint for band names.

    Returns:
        list: List of band name strings
    """
    headers = {
        'User-Agent': 'FW-BandName-Generator/1.0 (https://github.com/yourrepo)',
        'Accept': 'application/json'
    }

    params = {
        'query': SPARQL_QUERY,
        'format': 'json'
    }

    print("Querying Wikidata SPARQL endpoint...")
    response = requests.get(WIKIDATA_SPARQL_ENDPOINT, params=params, headers=headers)
    response.raise_for_status()

    data = response.json()
    results = data.get('results', {}).get('bindings', [])

    bands = []
    for result in results:
        band_name = result.get('itemLabel', {}).get('value')
        if band_name:
            bands.append(band_name)

    return bands


def main():
    """Main execution function"""
    print("=" * 60)
    print("Wikidata Band Names Fetcher (Day 1 - Test Version)")
    print("=" * 60)

    try:
        bands = fetch_bands_from_wikidata()

        print(f"\n✓ Successfully fetched {len(bands)} band names from Wikidata\n")
        print("Sample results:")
        print("-" * 60)
        for i, band in enumerate(bands[:20], 1):
            print(f"{i:3d}. {band}")

        if len(bands) > 20:
            print(f"... and {len(bands) - 20} more bands")

        print("-" * 60)
        print(f"\nTotal bands fetched: {len(bands)}")

    except requests.exceptions.RequestException as e:
        print(f"✗ Error querying Wikidata: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
