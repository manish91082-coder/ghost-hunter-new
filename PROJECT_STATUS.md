# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest signer-regression commit: `919e72cf6099ccb4fc5f6ff8ac1151bd5ec51c8f`
- Latest CI-hardening commit: `7f6aaeb331ea679738b01ce89ee6b44ed3ca5ee8`
- Certification PR: `#1` (OPEN, ready for review, base `master`)
- Current PR head: `2e406935752dddacb2d7c4cf820697840b002f68`
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, least-privilege/time-bounded CI execution, and rejection of an all-zero signer private key.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and on pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

A fresh signer regression commit was added to trigger the normal certification path: `919e72cf6099ccb4fc5f6ff8ac1151bd5ec51c8f`. The connector still exposes zero authoritative workflow runs for that commit, so **no CI pass is claimed**.

Historical GREEN runs remain historical evidence only and are not current-head certification.

## 5. CURRENT REORG / SETTLEMENT INTEGRITY HARDENING
`phantomx/recovery_coordinator.py` deliberately returns `BLOCK` for terminal `PROFIT_CONFIRMED` and `PROFIT_FAILED` states. Regression coverage explicitly verifies that both terminal states remain blocked even when incoming chain evidence is `REORGED`.

This preserves the fail-closed property while a later phase designs any controlled settlement invalidation/re-observation mechanism required for real canonical-chain reorg handling. No automatic reopening or profit reversal has been introduced.

## 6. CURRENT BLOCKERS / P0 GATES
1. **Authoritative current-head CI**: not exposed by current connector path.
2. **Controlled production signer identity proof** without exposing private key material.
3. **Controlled production Polygon network/provider authority proof** using explicitly approved production endpoints and the deployed executor address.
4. **Production private relay capability** with no public fallback.
5. **Startup/recovery safety under production-like conditions**, including a production-grade settlement reorg policy.
6. **Controlled shadow/staging evidence** using the identical immutable artifact chain.
7. **Final realized live PnL evidence** after all preceding gates are GREEN.
8. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, logs, and chat.

## 7. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 8. DISTANCE-TO-GOAL SCORECARD
These are explicit planning metrics, not claims of external evidence.

### A. Engineering foundation
- Deterministic Phase-19 execution-integrity implementation: **substantially built**.
- Practical assessment: **~85% engineering foundation complete**.
- Current-head certification: **0% certified** until an authoritative run result exists.

### B. First real-life hunt readiness
Required pre-hunt gates are current-head CI, controlled signer identity, approved Polygon/provider authority, private relay, production-like startup/recovery + reorg policy, and identical-artifact shadow/staging evidence.
- GREEN gates today: **0 / 6**.
- First real-money hunt: **NOT READY**.

### C. Continuous hunting readiness
Continuous hunting additionally requires verified realized PnL from the first hunt and safe repeatability across nonce lifecycle, replacement/drop, restart/recovery, reorg handling, and operational observability.
- Verified live cycles: **0**.
- Continuous hunting: **NOT ACHIEVED**.

### D. One-line position
**Codebase: ~85% foundation complete. First real-life hunt: 0/6 production prerequisites GREEN. Continuous hunting: 0 verified live cycles.**

## 9. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** next-sequence signer-boundary hardening to force a real certification-triggering code change.

**New work completed:**
- Added regression coverage that an all-zero 32-byte private key is rejected by the concrete EIP-1559 signer.
- Committed as `919e72cf6099ccb4fc5f6ff8ac1151bd5ec51c8f`.
- Checked the resulting commit for PR workflow visibility; connector currently returns no workflow run, so CI remains UNKNOWN.
- Kept live signing, broadcast, capital, and production authorization locked.

**Current verdict:** the next sequence step has been exercised at the code level, but external CI evidence is still absent. No launch gate is considered GREEN merely because the code change is plausible.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** obtain authoritative CI result for the current PR head. If GREEN, advance to controlled signer/provider/relay/shadow gates. If FAILURE, freeze and diagnose.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
