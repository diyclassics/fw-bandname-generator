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
    Query Wikidata SPARQL endpoint for a batch of band Q-IDs and labels.

    Args:
        offset: Starting position for pagination
        limit: Number of results to fetch

    Returns:
        list: List of tuples (qid, label) where qid is like 'Q215380'
    """
    headers = {
        "User-Agent": "FW-BandName-Generator/1.0 (https://github.com/yourrepo)",
        "Accept": "application/json",
    }

    query = SPARQL_QUERY_TEMPLATE.format(limit=limit, offset=offset)
    params = {"query": query, "format": "json"}

    response = requests.get(WIKIDATA_SPARQL_ENDPOINT, params=params, headers=headers)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", {}).get("bindings", [])

    bands = []
    for result in results:
        # Extract Q-ID from item URI (e.g., http://www.wikidata.org/entity/Q215380 -> Q215380)
        item_uri = result.get("item", {}).get("value", "")
        qid = item_uri.split("/")[-1] if item_uri else None

        # Extract label
        label = result.get("itemLabel", {}).get("value")

        if qid and label:
            bands.append((qid, label))

    return bands


def fetch_bands_from_wikidata():
    """
    Query Wikidata SPARQL endpoint for all bands with pagination.

    Returns:
        dict: Dictionary mapping Q-ID to label {qid: label}
    """
    all_bands = {}  # {qid: label}
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

                # Add to dict (automatically deduplicates by Q-ID)
                for qid, label in batch:
                    all_bands[qid] = label

                pbar.update(1)
                pbar.set_postfix({"total_unique": len(all_bands)})

                # Check if we got fewer results than batch size (last batch)
                if len(batch) < BATCH_SIZE:
                    break

                offset += BATCH_SIZE

                # Rate limiting - be nice to Wikidata
                time.sleep(RATE_LIMIT_DELAY)

            except requests.exceptions.RequestException as e:
                print(f"\n✗ Error fetching batch at offset {offset}: {e}")
                break

    print(f"\n✓ Fetched {len(all_bands)} unique bands (by Q-ID)")

    return all_bands


def load_existing_bands_txt(filepath):
    """
    Load existing bands.txt and convert to TSV format with LOCAL IDs.

    Args:
        filepath: Path to existing bands.txt file

    Returns:
        dict: Dictionary mapping ID to label {id: label}
    """
    import os
    import re

    bands_dict = {}

    if not os.path.exists(filepath):
        print(f"No existing file at {filepath}, starting fresh")
        return bands_dict

    print(f"Loading existing bands from {filepath}...")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Pattern to detect Q-IDs
    q_pattern = re.compile(r"^Q\d+$")

    local_counter = 1
    for line in lines:
        if q_pattern.match(line):
            # Already a Q-ID, keep as-is
            bands_dict[line] = line
        else:
            # Regular band name, assign LOCAL ID
            local_id = f"LOCAL_{local_counter:06d}"
            bands_dict[local_id] = line
            local_counter += 1

    print(f"✓ Loaded {len(bands_dict)} existing bands")
    return bands_dict


def merge_bands(existing_bands, wikidata_bands):
    """
    Merge existing bands with Wikidata results.

    Args:
        existing_bands: dict {id: label} from existing file
        wikidata_bands: dict {qid: label} from Wikidata

    Returns:
        dict: Merged dictionary {id: label}
    """
    merged = existing_bands.copy()

    new_count = 0
    for qid, label in wikidata_bands.items():
        if qid not in merged:
            merged[qid] = label
            new_count += 1

    print(f"✓ Added {new_count} new bands from Wikidata")
    print(f"✓ Total bands after merge: {len(merged)}")

    return merged


def write_tsv(bands_dict, filepath):
    """
    Write bands dictionary to TSV file.

    Args:
        bands_dict: Dictionary {id: label}
        filepath: Output TSV file path
    """
    import os

    # Sort: LOCAL entries first (alphabetical), then Q entries (by numeric ID)
    def sort_key(item):
        id_str, _ = item
        if id_str.startswith("LOCAL_"):
            return (0, id_str)  # LOCAL entries first
        elif id_str.startswith("Q"):
            try:
                return (1, int(id_str[1:]))  # Q entries by numeric value
            except ValueError:
                return (2, id_str)  # Fallback for malformed Q-IDs
        else:
            return (3, id_str)  # Other entries last

    sorted_bands = sorted(bands_dict.items(), key=sort_key)

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        for band_id, label in sorted_bands:
            f.write(f"{band_id}\t{label}\n")

    print(f"✓ Wrote {len(sorted_bands)} bands to {filepath}")


def write_txt_from_tsv(tsv_filepath, txt_filepath):
    """
    Generate bands.txt from bands.tsv for backward compatibility.

    Args:
        tsv_filepath: Input TSV file path
        txt_filepath: Output TXT file path
    """
    labels = []

    with open(tsv_filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split("\t")
                if len(parts) == 2:
                    labels.append(parts[1])

    with open(txt_filepath, "w", encoding="utf-8") as f:
        for label in labels:
            f.write(f"{label}\n")

    print(f"✓ Generated {txt_filepath} with {len(labels)} band names")


def main():
    """Main execution function"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Update band names from Wikidata")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--output",
        default="static/data/bands.tsv",
        help="Output TSV file path (default: static/data/bands.tsv)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Wikidata Band Names Updater")
    print("=" * 60)

    try:
        # Load existing bands
        txt_path = "static/data/bands.txt"
        existing_bands = load_existing_bands_txt(txt_path)

        # Fetch from Wikidata
        wikidata_bands = fetch_bands_from_wikidata()

        # Merge
        merged_bands = merge_bands(existing_bands, wikidata_bands)

        if args.dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN - No files will be written")
            print("=" * 60)
            print(f"Would write {len(merged_bands)} bands to {args.output}")
            print(f"Would generate {txt_path} from TSV")
            print("\nSample output (first 10 LOCAL, first 10 Q):")
            print("-" * 60)

            local_entries = [(k, v) for k, v in merged_bands.items() if k.startswith("LOCAL_")]
            q_entries = [(k, v) for k, v in merged_bands.items() if k.startswith("Q")]

            for i, (id_str, label) in enumerate(local_entries[:10], 1):
                print(f"{i:3d}. {id_str}\t{label}")
            if local_entries:
                print("    ...")
            for i, (id_str, label) in enumerate(q_entries[:10], 1):
                print(f"{i:3d}. {id_str}\t{label}")

        else:
            # Write TSV
            write_tsv(merged_bands, args.output)

            # Generate TXT for backward compatibility
            write_txt_from_tsv(args.output, txt_path)

            print("\n" + "=" * 60)
            print("✓ Update complete!")
            print("=" * 60)

    except requests.exceptions.RequestException as e:
        print(f"✗ Error querying Wikidata: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
