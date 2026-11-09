# HS23 table generator

Script that generates the pre-aggregated snapshot of the HEPiX HEPScore23 (HS23) scores table bundled
with DIRAC (`src/DIRAC/WorkloadManagementSystem/Client/data/HS23scores.json`), plus its tests.

The DIRAC repository runs it nightly (`.github/workflows/hs23-table-update.yml`): it downloads the
HEPiX CSV, validates it (broken rows are skipped and reported), aggregates it to one entry per
(normalized CPU model, SMT state) with a `# Meas`-weighted mean of `Score/Ncores`, and writes
deterministic JSON with provenance (source URL, source content hash, data-as-of date). DIRAC then
opens or updates a PR whenever the derived table changed — new CPU models or score changes — never
merged automatically.

Context: DIRACGrid/DIRAC#8871 (issue) and DIRACGrid/DIRAC#8870 (PR), ADR
`docs/adr/0001-hs23-cpu-power-from-hepix-table.md` in the DIRAC repository.

## Usage

```bash
python generate_hs23_table.py --output HS23scores.json
python generate_hs23_table.py --csv-file HS23scores.csv --output HS23scores.json  # offline
```

## Tests

```bash
pytest hs23-table/test_generate_hs23_table.py
```

One test pins `normalize_cpu_model` to be idempotent and in sync with
`DIRAC.WorkloadManagementSystem.Client.HS23Table.normalizeCpuModel` — the two implementations must
not drift (DIRAC additionally matches on the original CSV strings as a safety net).
