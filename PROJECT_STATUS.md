# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest implementation: `5c926b91a5e551bb7353ed60da591b6e69743638`
- Recovered-settlement certification `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Adapter adversarial tests: `5c926b91...`
- Fresh adapter certification `#423`: **IN PROGRESS**
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## VERIFIED CAPABILITIES
Deterministic economics, immutable authorization/envelope binding, quote and simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, private-only submission, recovery, receipt reconciliation, executor controls, and authority quorum/provenance/freshness controls are implemented. #420 certified the recovered-settlement repair.

The production chain observer is read-only. It verifies Polygon identity, gathers transaction/receipt/pending-nonce evidence, validates receipt block canonicality, groups provider observations deterministically, and requires a unique quorum-backed decision. It has no signing or submission dependency.

The HTTP read-only transport permits transaction and receipt lookup methods required by the observer while submission/write methods remain blocked before network I/O.

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof.
3. Controlled production private relay proof.
4. Production-like recovery and settlement reorg evidence, including transaction/receipt quorum certification and durable integration.
5. Controlled shadow/staging evidence.
6. Final realized live PnL evidence.
7. Live mainnet capital remains forbidden.

## CHECKPOINT
#420 GREEN certified the recovered-settlement repair. The read-only production transaction/receipt quorum boundary is implemented and its adversarial tests are attached to branch head `5c926b91...`.

Fresh workflow `#423` is currently running against `a5f17ed...`, with no GREEN claim yet. Run #422 separately certified the read-only RPC allowlist change at `64f96d8b...`.

## NEXT ACTION
Complete fresh certification for `#423`. On GREEN, integrate the quorum-backed observation evidence into durable chain-observation persistence so recovered settlement cannot consume a single-provider observation.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
