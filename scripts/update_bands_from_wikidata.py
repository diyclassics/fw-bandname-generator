#!/usr/bin/env python3
"""
Wikidata Band Names Automation Script

Fetches band names from Wikidata's SPARQL endpoint and updates static/data/bands.txt
"""

import requests
import time
from tqdm import tqdm


WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
BATCH_SIZE = 10000
RATE_LIMIT_DELAY = 1  # seconds between requests

# SPARQL query template for musical groups/bands (Q215380)
# {offset} will be replaced with actual offset value
SPARQL_QUERY_TEMPLATE = """
SELECT DISTINCT ?item ?itemLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q215380 .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit} OFFSET {offset}
"""


def fetch_bands_batch(offset=0, limit=BATCH_SIZE):
    """
    Query Wikidata SPARQL endpoint for a batch of band names.

    Args:
        offset: Starting position for pagination
        limit: Number of results to fetch

    Returns:
        list: List of band name strings
    """
    headers = {
        'User-Agent': 'FW-BandName-Generator/1.0 (https://github.com/yourrepo)',
        'Accept': 'application/json'
    }

    query = SPARQL_QUERY_TEMPLATE.format(limit=limit, offset=offset)
    params = {
        'query': query,
        'format': 'json'
    }

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


def fetch_bands_from_wikidata():
    """
    Query Wikidata SPARQL endpoint for all band names with pagination.

    Returns:
        set: Set of unique band names (normalized to lowercase for deduplication)
    """
    all_bands = set()
    offset = 0

    print("Fetching bands from Wikidata...")
    print(f"Using batch size: {BATCH_SIZE}")

    # Create progress bar (we don't know total upfront, so use unknown total)
    with tqdm(desc="Fetching batches", unit="batch") as pbar:
        while True:
            try:
                batch = fetch_bands_batch(offset=offset, limit=BATCH_SIZE)

                if not batch:
                    # No more results
                    break

                # Add to set (automatically deduplicates, case-sensitive for now)
                for band in batch:
                    # Normalize to lowercase for deduplication
                    all_bands.add(band.lower())

                pbar.update(1)
                pbar.set_postfix({'total_unique': len(all_bands)})

                # Check if we got fewer results than batch size (last batch)
                if len(batch) < BATCH_SIZE:
                    break

                offset += BATCH_SIZE

                # Rate limiting - be nice to Wikidata
                time.sleep(RATE_LIMIT_DELAY)

            except requests.exceptions.RequestException as e:
                print(f"\n✗ Error fetching batch at offset {offset}: {e}")
                break

    print(f"\n✓ Fetched {len(all_bands)} unique bands (after deduplication)")

    # Convert back to list for compatibility
    return list(all_bands)


def main():
    """Main execution function"""
    print("=" * 60)
    print("Wikidata Band Names Fetcher (Day 2 - Full Fetch)")
    print("=" * 60)

    try:
        bands = fetch_bands_from_wikidata()

        print("\nSample results (first 20):")
        print("-" * 60)
        for i, band in enumerate(sorted(bands)[:20], 1):
            print(f"{i:3d}. {band}")

        if len(bands) > 20:
            print(f"... and {len(bands) - 20} more bands")

        print("-" * 60)
        print(f"\n✓ Total unique bands fetched: {len(bands)}")

    except requests.exceptions.RequestException as e:
        print(f"✗ Error querying Wikidata: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
