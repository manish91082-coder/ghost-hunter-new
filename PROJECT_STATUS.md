# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest implementation: `86bb4786c11c75312d3090047468a07799ac2e36`
- Recovered-settlement certification `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Adapter adversarial certification `#423`: **GREEN**
- Durable quorum observation admission store: `9cd129c26c23b62d5ae0e7ea796f070fd7802c9c`
- Durable quorum admission tests: `8dc6d111...` lineage restored on branch by equivalent direct commit
- Execution-observation quorum gate: `2a02e9110f303befa1fba2b0311f0e321530f0ba`
- Quorum execution-observation contract tests: `86bb4786...`
- Prior certification `#424`: **FAILED** because the branch head running that workflow referenced `phantomx.production_chain_observation_store` but that file was not actually present on the branch; five unittest modules failed at import time. Solidity/EVM and Polygon fork stages were GREEN.
- Repair run `#426`: **IN PROGRESS** on `86bb4786...`; store and quorum-gate contract coverage are now present on the actual branch.
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

The execution-observation entry point exposes a dedicated quorum-gated persistence path. It first requires the exact, previously persisted and fresh quorum record, verifies transaction/state/replacement identity, and only then delegates to the existing durable chain-observation persistence. The full canonical block evidence remains supplied separately to preserve receipt canonicality validation. fileciteturn1465file0L2-L2

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like recovery and settlement reorg evidence, including complete certification of quorum-gated transaction/receipt observation.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
`#423` is GREEN for the read-only production transaction/receipt quorum observer. The durable quorum evidence store is now physically present on the active branch, and the execution-observation quorum gate is also present there. The first attempt to certify that gate exposed a branch-integration defect rather than a semantic test failure: `#424` executed commit `2a02e911...`, whose import boundary referenced a store file that was not on that branch lineage. fileciteturn1456file0L1-L2

The branch was repaired by adding the missing durable store as `9cd129c2...` and adding corrected quorum-gate contract tests as `86bb4786...`. The deterministic test intent now exposes the required `intent_hash()` method instead of using an invalid placeholder object.

## NEXT ATOMIC ACTION
Wait for fresh certification `#426` on `86bb4786...`. If GREEN, perform the next structural integration audit across recovery call sites and make every production recovery-to-settlement path require the quorum-gated observation admission, then add the end-to-end single-provider isolation fixture and re-certify.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
