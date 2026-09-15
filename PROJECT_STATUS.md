# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest implementation: `6a3bbc63e1c4a99477136a6329e8f34cda0e705c`
- Recovered-settlement certification `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Adapter tests: `6a3bbc63...`
- Fresh adapter certification: **PENDING**
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Production readiness: **NOT ACHIEVED**

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## VERIFIED CAPABILITIES
Deterministic economics, immutable authorization/envelope binding, quote/simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, private-only submission, recovery, receipt reconciliation, executor controls, and authority quorum/provenance/freshness controls are implemented. #420 certified the recovered-settlement repair.

The new production chain observer is read-only. It verifies Polygon identity, gathers transaction/receipt/pending-nonce evidence, validates receipt block canonicality, groups provider observations deterministically, and requires a unique quorum-backed decision. It has no signing or submission dependency.

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof.
3. Controlled production private relay proof.
4. Production-like recovery and settlement reorg evidence, including transaction/receipt quorum certification and durable integration.
5. Controlled shadow/staging evidence.
6. Final realized live PnL evidence.
7. Live mainnet capital remains forbidden.

## CHECKPOINT
#420 GREEN certified the recovered-settlement repair. `77c3c457...`, `64f96d8b...`, and `6a3bbc63...` add and test the read-only transaction/receipt quorum boundary. Fresh certification of that boundary is pending.

## NEXT ACTION
Complete fresh Phase-19 certification for `6a3bbc63...`. On GREEN, integrate quorum-backed chain-observation evidence with durable persistence so recovered settlement cannot consume a single-provider observation.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
