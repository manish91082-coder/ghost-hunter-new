# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest implementation: `06af4ed4cae9bcb9f9ecbe9ab44a65fbfe526226`
- Recovered-settlement certification `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Adapter adversarial certification `#423`: **GREEN**
- Durable quorum observation admission store: `05ac3286752b8fe1f00880ab103b616819c9f4a7`
- Durable quorum admission tests: `8dc6d111...`
- Execution-observation quorum gate: `2a02e9110f303befa1fba2b0311f0e321530f0ba`
- Quorum execution-observation contract tests: `06af4ed4...`
- Fresh certification for the quorum-gated observation layer: **PENDING**
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## VERIFIED CAPABILITIES
Deterministic economics, immutable authorization/envelope binding, quote and simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, private-only submission, recovery, receipt reconciliation, executor controls, and authority quorum/provenance/freshness controls are implemented. #420 certified the recovered-settlement repair and #423 certified the production chain observation adapter.

The production chain observer is read-only. It verifies Polygon identity, gathers transaction/receipt/pending-nonce evidence, validates receipt block canonicality, groups provider observations deterministically, and requires a unique quorum-backed decision. It has no signing or submission dependency. fileciteturn1368file0L1-L2

The HTTP read-only transport permits the transaction and receipt lookup methods required by the observer while submission/write methods remain blocked before network I/O. fileciteturn1344file0L3-L12

The durable quorum admission boundary stores the exact intent/transaction binding, decision state, common observed block, attesting provider names, and evidence hash, and provides an exact/fresh reuse check. fileciteturn1411file0L2-L2

The execution-observation entry point now exposes a dedicated quorum-gated persistence path. It first requires the exact, previously persisted and fresh quorum record, verifies transaction/state/replacement identity, and only then delegates to the existing durable chain-observation persistence. The full canonical block evidence remains supplied separately to preserve receipt canonicality validation. 

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like recovery and settlement reorg evidence, including complete certification of quorum-gated transaction/receipt observation.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
`#423` is GREEN for the read-only production transaction/receipt quorum observer. The durable quorum evidence store was added in `05ac3286...` and its persistence/reuse tests in `8dc6d111...`.

`2a02e911...` adds the quorum-gated execution-observation path. `06af4ed4...` adds contract tests proving quorum admission is required before lifecycle persistence and that state/replacement mismatches are blocked before admission. Fresh full-workflow certification has not yet returned.

## NEXT ATOMIC ACTION
Complete fresh Phase-19 certification for `06af4ed4...`. On GREEN, replace the remaining production recovery call sites with the quorum-gated observation path and add an end-to-end recovery fixture proving a single-provider observation cannot reach durable settlement reconciliation.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
