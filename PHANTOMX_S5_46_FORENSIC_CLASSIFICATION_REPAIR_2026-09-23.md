# PHANTOMX S5 #46 FORENSIC — TILE CLASSIFICATION PARITY REPAIR
# 2026-09-23

## Run identity
- Workflow: PHANTOMX S5 Curve Uniswap V3 Live Hunt
- Run: 35875307284 (#46)
- Exact HEAD: acf96579c03ef05dcc1457ac66573e3fc8f50b09
- Artifact: 10759348462
- Artifact SHA256: 520478e6d1dc2d292d38535177fe1ce5993fe65ee02e212adc4766ed9756ff40
- Terminal workflow conclusion: FAILURE because the scanner returned exit code 2.

## Forensic facts
- Expected tiles: 164
- Completed: 14 COMPLETE + 2 COMPLETE_NO_COMMON_ROUTE = 16
- Incomplete: 148
- Route observations: 532
- Gross-positive: 0
- Best gross: -4.452314 USDC
- Retryable failures: 1,319
- Terminal failures: 4,288
- Pair universe: COMPLETE_RECENT_WINDOW
- economic_certification: NOT_PERFORMED
- profit_claim: NONE
- This run is incomplete evidence and is NOT market-negative proof.

## Root cause / parity finding
RPCSemanticRevertConsensusError is deliberately terminal in phantomx/opportunity_discovery.py, but scripts/s5_curve_uv3_live_scan.py did not classify its message as a terminal no-route condition. The artifact contains one tile with 38/38 terminal ambiguous-revert-consensus failures and zero observations that was therefore labeled PARTIAL_INCOMPLETE. A smaller terminal execution reverted: SPL pattern also lacked explicit S5 parity.

This repair changes only the S5 tile classifier and its deterministic tests. It does not broaden the search, relax fail-closed coverage, alter RPC retry bounds, change economics, enable signing, or permit broadcast.

## Evidence boundary
The remaining 1,319 retryable failures are intentionally NOT reclassified by this repair. They remain an independent RPC-capacity/recovery gate and must be measured again after the parity fix.