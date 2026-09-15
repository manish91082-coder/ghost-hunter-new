# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest implementation: `d018f8aea32d7db5aa012b02dcaacab87435af4c`
- Recovered-settlement certification `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Adapter adversarial certification `#423`: **GREEN**
- Durable quorum observation admission store: `9cd129c26c23b62d5ae0e7ea796f070fd7802c9c`
- Execution-observation quorum gate: `2a02e9110f303befa1fba2b0311f0e321530f0ba`
- Fresh certification `#427`: **GREEN**
- End-to-end quorum recovery isolation certification `#430`: **GREEN**
- Settlement reconciliation quorum boundary: `6a48ed044cc1579116b75e3f801e6fa866f2e89b`
- Quorum settlement reconciliation certification `#432`: **GREEN**
- Quorum recovery provenance boundary: `03e2c93ee8b1116d38b81332f45f84265b4a5c3d`
- Quorum recovery provenance certification `#435`: **GREEN**
- Final Phase-19 adversarial recovery/settlement matrix: `d018f8aea32d7db5aa012b02dcaacab87435af4c`
- Fresh certification for final matrix: **PENDING / RUN NOT YET SURFACED**
- Matrix fixture hardening: isolated fixture recreation now uses registered cleanup rather than manually tearing down a fixture whose cleanup remains registered; final matrix explicitly exercises PENDING, REVERTED, DROP, REPLACED, and REORGED paths.
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## VERIFIED CAPABILITIES
Deterministic economics, immutable authorization/envelope binding, quote and simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, private-only submission, recovery, receipt reconciliation, executor controls, and authority quorum/provenance/freshness controls are implemented. #420, #423, #427, #430, #432, and #435 provide the latest certified gates.

The production chain observer is read-only and requires a unique quorum-backed decision. fileciteturn1534file0L2-L2

The execution-observation path requires an exact, previously persisted and fresh quorum record before lifecycle persistence. fileciteturn1545file0L2-L2

Settlement reconciliation now has a dedicated quorum boundary, and the lower-level settlement primitive is explicitly treated as an already-admitted path. fileciteturn1548file0L2-L2

Recovery mutation now has the same quorum provenance boundary for DROP, REPLACED, and REORGED evidence. fileciteturn1549file0L2-L2

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like recovery and settlement reorg evidence, including complete certification of quorum-gated transaction/receipt observation, settlement admission, and recovery provenance.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
`#435` is GREEN for quorum recovery provenance, including single-provider rejection, fresh two-provider admission, stale/future evidence rejection, replacement binding checks, reorg admission, and the static production-surface bypass audit. fileciteturn1536file0L2-L2

The final adversarial matrix was previously committed at `8460c589...`. Its certification had not surfaced in the Actions index, so the fixture was hardened before accepting any certification claim. Commit `d018f8aea32d7db5aa012b02dcaacab87435af4c` removes the double-teardown hazard by centralizing fixture recreation and explicitly adds fresh REPLACED and REORGED coverage alongside the already present PENDING, REVERTED, DROP, stale/future/tampered, canonical-block, settlement-conflict, restart, and low-level caller-confinement checks.

## NEXT ATOMIC ACTION
Obtain and verify the fresh Phase-19 certification for `d018f8aea32d7db5aa012b02dcaacab87435af4c`. On GREEN, begin the production-readiness gate audit. On failure, repair only the exact failing boundary and recertify.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
