#!/usr/bin/env python
"""Generate the pre-aggregated HS23 score table shipped with DIRAC.

Downloads the HEPiX HEPScore23 scores CSV, validates it, aggregates it to one
entry per (normalized CPU model, SMT state) and writes the JSON file that
DIRAC bundles as ``src/DIRAC/WorkloadManagementSystem/Client/data/HS23scores.json``
(see DIRAC's ``HS23Table.py`` and ``docs/adr/0001-hs23-cpu-power-from-hepix-table.md``).

The aggregation is a ``# Meas``-weighted mean of ``Score/Ncores`` over all rows
matching the key, mirroring what the HEPiX table publishes per server.

Usage:
    python generate_hs23_table.py --output HS23scores.json
    python generate_hs23_table.py --csv-file HS23scores.csv --output HS23scores.json

The output is deterministic for a given CSV content (sorted entries, stable
model-string choice), so a plain diff tells whether anything changed.
"""

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import requests

DEFAULT_CSV_URL = "https://raw.githubusercontent.com/HEPiX-Forum/hepix-forum.github.io/master/_data/HS23scores.csv"

REQUIRED_COLUMNS = ("CPU", "SMT enabled", "Score/Ncores", "# Meas")


def normalize_cpu_model(model):
    """Normalize a CPU model string for use as lookup key.

    Must stay in sync with ``DIRAC.WorkloadManagementSystem.Client.HS23Table.normalizeCpuModel``:
    lower-case everything, drop the frequency suffix, squash the spacing
    variants of ``(R)`` and collapse repeated whitespace.
    """
    model = model.lower()
    model = model.split("@", 1)[0]
    model = re.sub(r"\s*\(r\)\s*", "(r)", model)
    model = re.sub(r"\s+", " ", model).strip()
    return model


def parse_rows(text):
    """Parse the CSV into rows, skipping and reporting unparsable ones.

    :return: (rows, anomalies) with rows a list of dicts and anomalies a list
             of (reason, raw row) tuples
    """
    rows = []
    anomalies = []
    reader = csv.DictReader(io.StringIO(text))
    missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"CSV is missing the required column(s): {', '.join(missing)}")

    for raw in reader:
        try:
            cpu = (raw["CPU"] or "").strip()
            smt = int(raw["SMT enabled"])
            scorePerCore = float(raw["Score/Ncores"])
            measurements = int(raw["# Meas"] or 0)
            if not cpu or smt not in (0, 1) or scorePerCore <= 0 or measurements < 0:
                raise ValueError("out-of-range value")
            rows.append(
                {
                    "CPU": cpu,
                    "SMT": smt,
                    "ScorePerCore": scorePerCore,
                    "Measurements": measurements,
                    "first_date": (raw.get("first_date") or "").strip(),
                    "last_date": (raw.get("last_date") or "").strip(),
                }
            )
        except (KeyError, TypeError, ValueError) as err:
            anomalies.append((str(err), raw.get("CPU", raw)))
    return rows, anomalies


def aggregate(rows):
    """Combine the rows into one entry per (normalized model, SMT state).

    The per-core score is the ``# Meas``-weighted mean of ``Score/Ncores`` (rows
    with no measurement count weigh 1). The ``original`` model string kept for
    auditability is the shortest one seen, ties broken lexicographically, so
    that the output is deterministic.
    """
    groups = {}
    for row in rows:
        key = (normalize_cpu_model(row["CPU"]), row["SMT"])
        group = groups.setdefault(
            key,
            {
                "model": key[0],
                "original": row["CPU"],
                "smt": key[1],
                "weightedScore": 0.0,
                "weightSum": 0.0,
                "measurements": 0,
                "rows": 0,
                "first_date": "",
                "last_date": "",
            },
        )
        weight = float(row["Measurements"]) or 1.0
        group["weightedScore"] += weight * row["ScorePerCore"]
        group["weightSum"] += weight
        group["measurements"] += row["Measurements"]
        group["rows"] += 1
        if not group["first_date"] or (row["first_date"] and row["first_date"] < group["first_date"]):
            group["first_date"] = row["first_date"]
        if not group["last_date"] or (row["last_date"] and row["last_date"] > group["last_date"]):
            group["last_date"] = row["last_date"]
        if (len(row["CPU"]), row["CPU"]) < (len(group["original"]), group["original"]):
            group["original"] = row["CPU"]

    entries = []
    for group in sorted(groups.values(), key=lambda g: (g["model"], g["smt"])):
        entries.append(
            {
                "model": group["model"],
                "original": group["original"],
                "smt": group["smt"],
                "score_per_core": round(group["weightedScore"] / group["weightSum"], 1),
                "measurements": group["measurements"],
                "rows": group["rows"],
                "first_date": group["first_date"],
                "last_date": group["last_date"],
            }
        )
    return entries


def build_table(text, sourceUrl):
    """Build the output table dict from CSV text."""
    rows, anomalies = parse_rows(text)
    if not rows:
        raise ValueError("No parsable row in the CSV")
    entries = aggregate(rows)
    return {
        "source": sourceUrl,
        "source_hash": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        "data_as_of": max(entry["last_date"] for entry in entries if entry["last_date"]),
        "entries": entries,
    }, anomalies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-url", default=DEFAULT_CSV_URL, help="URL of the HEPiX HS23 scores CSV")
    parser.add_argument("--csv-file", help="read the CSV from this file instead of downloading it")
    parser.add_argument("--output", required=True, help="path of the JSON file to write")
    args = parser.parse_args()

    if args.csv_file:
        text = Path(args.csv_file).read_text()
    else:
        response = requests.get(args.csv_url, timeout=120)
        response.raise_for_status()
        text = response.text

    table, anomalies = build_table(text, args.csv_url)
    for reason, cpu in anomalies:
        print(f"ANOMALY: skipping row ({reason}): {cpu}", file=sys.stderr)

    output = Path(args.output)
    output.write_text(json.dumps(table, indent=2, ensure_ascii=False) + "\n")
    print(
        f"Wrote {len(table['entries'])} entries ({sum(entry['rows'] for entry in table['entries'])} rows,"
        f" {len(anomalies)} anomalies skipped) to {output}, data as of {table['data_as_of']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
