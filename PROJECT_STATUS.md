# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest implementation: `73f29f3912376b2beeeb3d8a5d974385ef7534c7`
- Recovered-settlement certification `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Adapter adversarial certification `#423`: **GREEN**
- Durable quorum observation admission store: `9cd129c26c23b62d5ae0e7ea796f070fd7802c9c`
- Durable quorum admission tests: `8dc6d111...` lineage restored on branch by equivalent direct commit
- Execution-observation quorum gate: `2a02e9110f303befa1fba2b0311f0e321530f0ba`
- Quorum execution-observation contract tests: `86bb4786...`
- Fresh certification `#427`: **GREEN**. All compile/EVM/Polygon stages and the Phase-19 unittest suite completed successfully.
- End-to-end quorum recovery isolation fixture repair certification `#430`: **GREEN**. The single-provider INCLUDED path was blocked before lifecycle persistence, while the broader suite completed successfully.
- Settlement reconciliation quorum boundary: `6a48ed044cc1579116b75e3f801e6fa866f2e89b`
- Quorum settlement reconciliation certification `#432`: **GREEN**. All compile/EVM/Polygon stages and the Phase-19 unittest suite completed successfully.
- Quorum recovery provenance boundary: `03e2c93ee8b1116d38b81332f45f84265b4a5c3d`
- Quorum recovery provenance tests: `73f29f3912376b2beeeb3d8a5d974385ef7534c7`
- Fresh certification `#435`: **GREEN**. The quorum recovery provenance matrix and production-surface bypass audit completed successfully.
- Final Phase-19 adversarial recovery/settlement matrix: **IMPLEMENTATION IN PROGRESS**
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

The durable quorum admission boundary stores the exact intent/transaction binding, decision state, common observed block, attesting provider names, and evidence hash, and provides an exact/fresh reuse check. fileciteturn1466file0L2-L2

The execution-observation entry point exposes a dedicated quorum-gated persistence path. It first requires the exact, previously persisted and fresh quorum record, verifies transaction/state/replacement identity, and only then delegates to the existing durable chain-observation persistence. The full canonical block evidence remains supplied separately to preserve receipt canonicality validation. fileciteturn1465file0L2-L2

The recovery isolation fixture statically constrains plain observation lifecycle persistence to its intentional boundary and exercises a single-provider INCLUDED observation that is rejected by a two-provider admission policy before transaction lifecycle mutation. fileciteturn1503file0L2-L2

The settlement layer exposes a dedicated quorum-gated reconciliation boundary. The low-level settlement primitive is an already-admitted path, while the production boundary validates exact transaction/state/replacement binding and requires persisted, fresh quorum provenance before any settlement record or terminal profit state can be created. fileciteturn1510file0L2-L2

The durable recovery layer exposes a matching quorum-gated boundary for DROP, REPLACED, and REORGED evidence. It validates exact state/transaction/replacement binding and fresh attester policy before calling the existing durable recovery mutation primitive. fileciteturn1527file0L2-L2

The certified recovery provenance matrix covers single-provider rejection, fresh two-provider DROP admission, stale replacement rejection, future REORG rejection, replacement binding mismatch, two-provider REORG admission, and a production-module static bypass audit. fileciteturn1530file0L2-L2

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like recovery and settlement reorg evidence, including complete certification of quorum-gated transaction/receipt observation, settlement admission, and recovery provenance.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
`#435` is GREEN. The fresh certification completed the quorum recovery provenance boundary and its adversarial matrix successfully, with the complete Phase-19 compile/EVM/Polygon and unittest workflow remaining GREEN. fileciteturn1536file0L2-L2

The next phase is now the final adversarial matrix. Its scope is deliberately broader than the already-certified isolated gates: it will exercise the complete recovery/settlement state family, provenance freshness and tamper resistance, canonical-block conflicts, evidence idempotency/conflict behavior, and persistence across restart before the production-readiness gate is considered.

## NEXT ATOMIC ACTION
Complete the final Phase-19 adversarial recovery/settlement matrix. Then, only on GREEN, perform the production-readiness gate audit for controlled signer identity, approved Polygon provider authority, private relay, shadow/staging, and realized-PnL evidence.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
