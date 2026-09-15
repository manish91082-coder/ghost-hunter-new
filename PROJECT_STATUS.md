# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest implementation: `02d22489685758659d577a3f878f108fb9b8632a`
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
- Quorum settlement reconciliation contract tests: `02d22489685758659d577a3f878f108fb9b8632a`
- Fresh certification `#432`: **IN PROGRESS**.
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

The settlement layer now exposes a dedicated quorum-gated reconciliation boundary. The low-level settlement primitive is explicitly documented as an already-admitted path, while the production boundary validates exact transaction/state/replacement binding and requires persisted, fresh quorum provenance before any settlement record or terminal profit state can be created. fileciteturn1510file0L2-L2

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like recovery and settlement reorg evidence, including complete certification of quorum-gated transaction/receipt observation and settlement admission.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
`#427` is GREEN for the repaired quorum-gated execution-observation contract layer. `#430` is also GREEN for the repaired end-to-end single-provider recovery isolation fixture. Its evidence showed that the admission gate blocks the single-provider path before downstream lifecycle persistence.

A deeper architectural audit then identified the next important boundary: settlement reconciliation itself must not be a standalone consumer of an unadmitted `ObservationDecision`. Commit `6a48ed04...` adds `reconcile_quorum_included_execution`, which validates the exact quorum binding and freshness policy before invoking the existing low-level settlement primitive. The corresponding contract tests are committed in `02d22489...`; fresh certification `#432` is now running on that head. fileciteturn1520file0L2-L2

## NEXT ATOMIC ACTION
Complete fresh certification `#432`. On GREEN, run the adversarial settlement matrix against quorum provenance: insufficient providers, stale evidence, future evidence, tx/state/replacement mismatch, canonical-block mismatch, conflicting settlement evidence, and successful two-provider admission. Then audit the replacement/reorg recovery paths for the same provenance requirement.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
