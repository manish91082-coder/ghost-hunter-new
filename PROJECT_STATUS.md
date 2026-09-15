# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest active-branch status checkpoint: `9591cc01a4e42672775b91696708742bb85035dd`
- Latest signer identity implementation commit: `fd34078fae864c02136484eeef3afd5f4a6c05a4`
- Latest repair commit: `148d9d01d0b6037312678d4af76ff1ade1a4e4e0`
- Fresh authoritative CI: run `#349` GREEN for `148d9d01...`
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, least-privilege/time-bounded CI execution, rejection of an all-zero signer private key, a non-secret signer identity challenge/proof boundary with cryptographic address recovery, and restored immutable signed-transaction artifact compatibility after CI failure diagnosis.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

Fresh authoritative run `#349` tested repair commit `148d9d01...` and concluded **SUCCESS**. The workflow job `phase19-tests` completed successfully through Solidity compile, Phase-19 EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full Phase-19 Python unittest stage.

Run `#348` remains historical failure evidence: it tested `fd34078f...`, passed compile/EVM/Polygon stages, then failed in Python because `SignedTransaction` had been removed during signer-proof hardening. The deterministic regression was repaired in `148d9d01...` and the repair is now GREEN in `#349`.

Historical GREEN runs remain historical evidence only and do not substitute for current implementation proof.

## 5. CURRENT SIGNER IDENTITY GATE
The concrete signer exposes a non-secret cryptographic challenge proof: an external verifier can supply a fresh 32-byte challenge, receive only a 65-byte signature, recover the Ethereum address, and compare it with the expected production signer address. The private key itself remains inside the signer and is never placed in the repository, logs, or chat.

The mechanism is now CI-certified, but the production signer identity gate is still **NOT GREEN** because no actual production signer identity has been independently challenged and evidenced yet.

## 6. CURRENT BLOCKERS / P0 GATES
1. **Controlled production signer identity proof** without exposing private key material.
2. **Controlled production Polygon network/provider authority proof** using explicitly approved production endpoints and the deployed executor address.
3. **Production private relay capability** with no public fallback.
4. **Startup/recovery safety under production-like conditions**, including a production-grade settlement reorg policy.
5. **Controlled shadow/staging evidence** using the identical immutable artifact chain.
6. **Final realized live PnL evidence** after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, logs, and chat.

## 7. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 8. DISTANCE-TO-GOAL SCORECARD
These are explicit planning metrics, not claims of external evidence.

### A. Engineering foundation
- Deterministic Phase-19 execution-integrity implementation: **substantially built**.
- Practical assessment: **~85% engineering foundation complete**.
- Fresh current implementation CI: **GREEN** on `148d9d01...` via run `#349`.

### B. First real-life hunt readiness
Required pre-hunt controls are fresh CI, controlled production signer identity, approved Polygon/provider authority, private relay, production-like startup/recovery + reorg, and identical-artifact shadow/staging evidence.
- Fresh current-implementation CI GREEN: **YES**.
- Production-control gates GREEN: **0 / 5**.
- First real-money hunt: **NOT READY**.

### C. Continuous hunting readiness
- Verified live cycles: **0**.
- Continuous hunting: **NOT ACHIEVED**.

## 9. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** fresh authoritative CI certification after the `SignedTransaction` repair, followed by synchronization of the certification branch and master continuity status files.

**New evidence:**
- Run `#349` targeted repair commit `148d9d01...` and concluded **SUCCESS**.
- The dedicated `phase19-tests` job completed all workflow stages successfully, including the Phase-19 Python unittest suite.
- The prior PR merge conflict was isolated to `PROJECT_STATUS.md`; the branch and master continuity anchors have now been synchronized to the same certified Phase-19 state.

**Current verdict:** the signer-proof implementation is CI-green and the stale status conflict has been resolved at the source file level. The actual production signer identity remains unproven and therefore blocked.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** establish a controlled non-secret production signer identity proof using an externally held signer and expected production address. Then proceed to approved Polygon/provider authority evidence. Do not expose private key material.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
