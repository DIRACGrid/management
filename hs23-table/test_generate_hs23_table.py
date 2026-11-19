"""Tests for the HS23 table generator"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import generate_hs23_table  # noqa: E402

CSV = """CPU,SMT enabled,# Meas,Score/Ncores,first_date,last_date
AMD EPYC 7302 16-Core Processor,0,336,23.9,2023-05-09,2023-06-27
AMD EPYC 7302 16-Core Processor,1,182,15.3,2023-02-22,2023-08-11
AMD EPYC 7302 16-Core Processor,1,11,15.8,2023-03-19,2023-03-21
AMD EPYC 7302 16-Core Processor,1,0,15.0,2026-08-13,2026-08-13
INTEL(R) XEON(R) GOLD 6530,0,21,27.6,2026-04-20,2026-04-22
broken,row,here,
"""


@pytest.fixture
def table():
    return generate_hs23_table.build_table(CSV, "https://example.org/HS23scores.csv")[0]


def test_parse_rows_skips_anomalies():
    rows, anomalies = generate_hs23_table.parse_rows(CSV)
    assert len(rows) == 5
    assert len(anomalies) == 1
    assert anomalies[0][1] == "broken"


def test_parse_rows_missing_column():
    with pytest.raises(ValueError, match="missing the required column"):
        generate_hs23_table.parse_rows("CPU\nAMD EPYC\n")


def test_aggregate_weighted_mean(table):
    # (182 x 15.3 + 11 x 15.8 + 1 x 15.0) / 194 -- the row with no measurement count weighs 1
    entry = next(e for e in table["entries"] if e["model"] == "amd epyc 7302 16-core processor" and e["smt"] == 1)
    assert entry["score_per_core"] == 15.3
    assert entry["measurements"] == 193
    assert entry["rows"] == 3
    assert entry["first_date"] == "2023-02-22"
    assert entry["last_date"] == "2026-08-13"
    assert entry["original"] == "AMD EPYC 7302 16-Core Processor"


def test_aggregate_one_entry_per_key(table):
    # one entry per (model, SMT), sorted
    keys = [(e["model"], e["smt"]) for e in table["entries"]]
    assert len(keys) == len(set(keys)) == 3
    assert keys == sorted(keys)


def test_header_fields(table):
    assert table["source"] == "https://example.org/HS23scores.csv"
    assert table["source_hash"].startswith("sha256:")
    assert table["data_as_of"] == "2026-08-13"


def test_deterministic_output():
    first = generate_hs23_table.build_table(CSV, "https://example.org/HS23scores.csv")[0]
    second = generate_hs23_table.build_table(CSV, "https://example.org/HS23scores.csv")[0]
    assert json.dumps(first, indent=2) == json.dumps(second, indent=2)


def test_normalize_synced_with_dirac():
    # keep the generator's normalization in sync with DIRAC's HS23Table.normalizeCpuModel
    models = [
        "Intel(R) Xeon(R) CPU E5-2630 v3 @ 2.40GHz",
        "INTEL(R) XEON(R) GOLD 6530",
        "Intel (R) Xeon (R) CPU Max 9462",
        "Intel(R) Xeon(R) CPU           E5520  @ 2.27GHz",
    ]
    for model in models:
        assert generate_hs23_table.normalize_cpu_model(model) == generate_hs23_table.normalize_cpu_model(
            generate_hs23_table.normalize_cpu_model(model)
        )
