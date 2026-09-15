# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest regression-bearing commit: `fbf2fbbc9f37eb89c0b9a0ccff6a56b4d60ecf50`
- Latest CI-hardening commit: `7f6aaeb331ea679738b01ce89ee6b44ed3ca5ee8`
- Certification PR: `#1` (OPEN, ready for review, base `master`)
- Phase: Phase 19 execution-integrity / E2E policy harness
- Live mainnet execution: **BLOCKED**
- Live capital authorization: **BLOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## 1. NON-NEGOTIABLE SAFETY / CONTROL RULES
- Evidence first; contradictory or missing evidence is UNKNOWN/BLOCKED.
- Fail closed on quote, proof, simulation, authorization, nonce, signer, relay, authority, or settlement inconsistency.
- AI is advisory and cannot override deterministic economics, preflight, governance, authorization, or settlement.
- Private execution has no public fallback.
- Live capital remains locked until every P0 gate has reproducible evidence.
- No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification.

## 2. CANONICAL PRODUCTION SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

Initial scope: Polygon, Aave V3, QuickSwap V2, Uniswap V3, USDC/WETH/WMATIC/WBTC, direct two-leg `A → B → A`.

## 3. VERIFIED IMPLEMENTATION CAPABILITIES
Phase 19 includes strict realized-profit gating, deterministic all-in economics, Keccak hashing, immutable intent/auth/envelope binding, exact block-bound quotes, route simulation and topology commitment, loan optimization, EVM preflight, Governor, signer boundary, durable SQLite nonce/transaction state, atomic replacement/recovery coordination, private-only submission, chain/recovery/reorg/replacement handling, receipt reconciliation, Solidity executor controls, Polygon fork harness, and adversarial/regression coverage.

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, and least-privilege/time-bounded CI execution.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and on pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

PR `#1` is open and ready for review solely to expose current-head PR checks. The current connector reports zero check-runs/workflow runs for the branch head, so **no CI pass is claimed**.

Historical GREEN runs remain historical evidence only and are not current-head certification.

## 5. CURRENT REORG / SETTLEMENT INTEGRITY HARDENING
`phantomx/recovery_coordinator.py` deliberately returns `BLOCK` for terminal `PROFIT_CONFIRMED` and `PROFIT_FAILED` states. Regression coverage explicitly verifies that both terminal states remain blocked even when incoming chain evidence is `REORGED`.

This preserves the fail-closed property while a later phase designs any controlled settlement invalidation/re-observation mechanism required for real canonical-chain reorg handling. No automatic reopening or profit reversal has been introduced.

## 6. CURRENT BLOCKERS / P0 GATES
1. Controlled production signer identity proof without exposing private key material.
2. Controlled production Polygon network/provider authority proof using explicitly approved production endpoints and the deployed executor address.
3. Production private relay capability with no public fallback.
4. Startup/recovery safety under production-like conditions, including a production-grade settlement reorg policy.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, logs, and chat.

## 7. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 8. DISTANCE-TO-GOAL SCORECARD
This section separates code completion from real-life hunting readiness. The percentages below are explicit planning metrics, not claims of external evidence.

### A. Engineering foundation
- Deterministic Phase-19 execution-integrity implementation: **substantially built**.
- Historical automated evidence exists, including prior GREEN Phase-19 runs, but these are not current-head certification.
- Current-head certification: **0% certified**, because current connector visibility shows no authoritative current-head check-run/workflow result.
- Practical assessment: **~85% engineering foundation complete**. This is a planning estimate based on the large set of already-implemented deterministic controls, not an independent test-derived percentage.

### B. First real-life hunt readiness
Required gates after the software foundation are: current-head CI, controlled signer identity, approved Polygon/provider authority, private relay, production-like startup/recovery + reorg policy, and identical-artifact shadow/staging evidence.
- GREEN gates among these required pre-hunt gates today: **0 / 6**.
- Therefore first real-money hunting readiness is **NOT READY**.
- No exact calendar distance is asserted because the remaining gates depend on controlled external infrastructure/evidence that is not present in the repository.

### C. Continuous hunting readiness
Continuous hunting additionally requires the first hunt to produce verified realized PnL and then prove safe repeatability, restart/recovery, nonce lifecycle, replacement/drop handling, reorg handling, and operational observability under repeated cycles.
- Continuous production evidence: **0 completed live cycles**.
- Continuous hunting readiness: **NOT ACHIEVED**.

### D. Simple answer in one line
**Codebase: ~85% foundation complete. First real-life hunt: 0/6 production prerequisites GREEN, so not launchable yet. Continuous hunting: 0 verified live cycles, so not achieved.**

## 9. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** explicit distance-to-hunting readiness scorecard.

**New work completed:**
- Added a clear separation between engineering foundation, first-hunt readiness, and continuous-hunt readiness.
- Recorded that current-head CI has **0% certification** because authoritative current-head check evidence is not exposed.
- Recorded that **0/6** pre-hunt production prerequisites are GREEN today.
- Recorded that continuous hunting has **0 verified live cycles**.
- Preserved the live-capital lock and all existing safety boundaries.

**Current verdict:** we are materially closer on the software/control foundation than on real-life launch. The remaining distance is dominated by controlled external evidence, not by adding random strategy features.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** clear authoritative current-head CI first; then close signer identity, approved Polygon/provider authority, private relay, production-like recovery/reorg, and shadow/staging gates in that order. Only after those are GREEN can the first controlled real-life hunt be considered.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
