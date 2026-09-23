# PHANTOMX S5 #44 PROVIDER POISONING REPAIR • 2026-09-23

## Terminal evidence

- Workflow: PHANTOMX S5 Curve <-> Uniswap V3 Live Hunt
- Run: #44 / ID 35863910575
- Executable HEAD: c2d93c28ee58c553516b0d067c5476069ebb4183
- Result: FAILURE with required artifact publication
- Artifact ID: 10751961217
- Artifact ZIP SHA-256: 3529759994c37249a4cfa02dbc18f00fafb593257d5bbb620376ea79efffb225

## Forensic result

- Declared/recorded tiles: 164 / 164
- Complete tiles: 3
- Incomplete tiles: 161
- Pair-universe status: COMPLETE_RECENT_WINDOW
- Retryable evaluation failures: 5,636
- Observations: 76
- Gross-positive observations: 0
- Best gross delta: -4.452314 USDC
- Economic certification: NOT_PERFORMED
- Profit claim: NONE

The run is incomplete infrastructure/evidence coverage. The observed negative spread is not a complete market certificate.

## Root cause

The provider-diversity repair succeeded: individual logical reads now rotate across distinct providers. The remaining dominant failure population is provider-local poisoning from HTTP 429/rate-limit responses and historical-state/capability failures. Those providers can continue to receive new tasks even after a local failure, causing repeated recovery exhaustion across the bounded tile fleet.

## Surgical repair

- Add a bounded 60-second provider-local temporary quarantine for 403/408/429, rate-limit/service-unavailable and historical-state/pruned capability failures.
- Preserve the existing long quarantine for explicit authentication/paid-plan failures.
- Preserve distinct-provider logical failover, per-provider max concurrency, two bounded recovery passes and fail-closed semantics.
- Do not change the S5 search domain, loan frontier, economics, signing, broadcast or capital rules.
- Add deterministic tests for 429 and historical-state provider quarantine.

## Required proof

1. Exact-head Phase-19 CI GREEN.
2. Fresh controlled S5 read-only hunt from that verified repair HEAD.
3. Terminal artifact with materially improved and complete declared coverage before S5 certification.
