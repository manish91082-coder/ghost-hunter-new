# PHANTOMX S3 COVERAGE REPAIR EVIDENCE
## 2026-09-21

### Finding

S3 Ramses V3 ↔ Uniswap V3 live-read run #17 (`35578078265`) completed at workflow level on trigger commit `34023ae5f88da0dec7ac3e837b89a5fd8ae39b1d`, but the published artifact was not complete market evidence.

The artifact declared:
- 7 active recent-window pairs.
- 6 Ramses tick spacings.
- 4 Uniswap V3 fee tiers.
- 168 declared tiles.
- 168/168 tiles `UNAVAILABLE_OR_FAILED`.
- 164 failures were deterministic `Ramses V3 pool does not exist for requested tick spacing`.
- 4 failures were `eth_call ... execution reverted: Unexpected error`.
- 0 route observations.
- `economic_certification=NOT_PERFORMED`.
- `profit_claim=NONE`.

Therefore the run was not treated as a market-negative certificate and not treated as complete S3 coverage.

### Root Cause

`scripts/s3_ramses_uv3_live_scan.py` previously caught every exception under a broad `Exception` boundary and labeled it `UNAVAILABLE_OR_FAILED`. It also returned exit code 0 whenever the failover pool produced any top-level result.

That behavior conflated:
1. deterministic structural route absence, which is complete evidence for that declared cell, and
2. unresolved RPC/semantic failures, which are incomplete evidence.

### Repair

Commit `0213dea08fffbc30256ded62dd5b91c28b605936`:

1. Added `classify_s3_tile_failure()`.
2. Classified deterministic missing-pool errors as `COMPLETE_NO_COMMON_ROUTE`.
3. Classified RPC, semantic, timeout, and other unresolved failures as `PARTIAL_INCOMPLETE`.
4. Added `summarize_s3_coverage()` with expected/observed/completed/incomplete tile counts.
5. Required exact declared tile cardinality plus zero incomplete tiles for aggregate `COMPLETE`.
6. Changed the scanner exit code to fail closed: 0 only for complete aggregate coverage, 2 for an incomplete aggregate with preserved evidence, 1 for no usable endpoint result.
7. Added import-path fallback so the S3 module can be imported by the Phase-19 unittest loader.

### Regression Coverage

Commit `3ea4d347f1d400232342f5f44c93a5a9948e93c8` adds `tests/phase19/test_s3_ramses_uv3_live_scan.py` covering:
- Ramses missing-pool terminal classification.
- Uniswap missing-pool terminal classification.
- RPC semantic revert as incomplete.
- Generic transport failure as incomplete.
- Complete aggregate with terminal no-route cells.
- Partial aggregate with an incomplete tile.
- Missing expected tiles as incomplete.

### Verification

Phase-19 run #982 / ID `35580051618` on `3ea4d347f1d400232342f5f44c93a5a9948e93c8` is GREEN. All workflow steps completed successfully, including Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full unittest suite. The suite reported 899 tests with 0 failures and 0 errors.

### Current Verification Run

S3 run #18 / ID `35579964402` runs the repaired scanner on commit `0213dea08fffbc30256ded62dd5b91c28b605936`. At the current checkpoint the run is still in progress, so no repaired S3 market result is claimed yet.

### Safety / Scope

This repair changes discovery evidence classification only. Signing, submission, public broadcast, live-capital access, and production authorization remain blocked.
