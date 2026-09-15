# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest signer identity implementation commit: `fd34078fae864c02136484eeef3afd5f4a6c05a4`
- Latest repair commit: `148d9d01d0b6037312678d4af76ff1ade1a4e4e0`
- Latest authoritative CI result: run `#345` GREEN for `919e72cf...`; subsequent signer-proof CI run `#348` FAILED on a concrete missing `SignedTransaction` definition/import break introduced during hardening.
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

Authoritative run `#345` tested `919e72cf...` and concluded **SUCCESS**: Solidity compile successful; **14/14 EVM**, **3/3 Polygon fork smoke**, **1/1 Polygon fork execution probe**, and **422/422 Python tests**, with **0 failures and 0 skips**. fileciteturn736file0

The next signer-proof certification run `#348` tested `fd34078f...` and **FAILED** during the Python suite. Compile, EVM, Polygon smoke, and Polygon execution probe all passed, but multiple Python modules failed to import because `phantomx.signer` no longer defined the existing `SignedTransaction` artifact type; two direct signer tests also raised `NameError: SignedTransaction is not defined`. The failure was isolated and repaired in commit `148d9d01...`; fresh CI certification is required for that repair. fileciteturn752file0

Historical GREEN runs remain historical evidence only and are not certification for the repaired current implementation.

## 5. CURRENT SIGNER IDENTITY GATE
The concrete signer now exposes a non-secret cryptographic challenge proof: an external verifier can supply a fresh 32-byte challenge, receive only a 65-byte signature, recover the Ethereum address, and compare it with the expected production signer address. The private key itself remains inside the signer and is never placed in the repository, logs, or chat.

The gate is **NOT GREEN**. The mechanism exists and the failure was caught by authoritative CI, but the repair itself has not yet completed a GREEN certification run, and no actual production signer identity has been challenged and independently evidenced.

## 6. CURRENT BLOCKERS / P0 GATES
1. **Fresh CI certification after the `SignedTransaction` repair**.
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
- Latest authoritative certification: **GREEN for pre-proof implementation**; newer signer-proof branch state is **BLOCKED pending fresh CI after repair**.

### B. First real-life hunt readiness
Required pre-hunt controls are fresh CI for the current implementation, controlled production signer identity, approved Polygon/provider authority, private relay, production-like startup/recovery + reorg, and identical-artifact shadow/staging evidence.
- Fresh current-implementation CI GREEN: **NO**.
- Production-control gates GREEN: **0 / 5** after fresh CI.
- First real-money hunt: **NOT READY**.

### C. Continuous hunting readiness
- Verified live cycles: **0**.
- Continuous hunting: **NOT ACHIEVED**.

## 9. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** forensic diagnosis and repair of the first fresh CI failure in signer-proof hardening.

**New evidence:**
- Authoritative run `#348` failed exactly on the newly hardened signer branch.
- The failure was not environmental noise: the test suite reached the Python phase and exposed a deterministic source regression, namely removal of the required `SignedTransaction` definition.
- All earlier CI stages in that run passed before the Python import/runtime failure.

**Repair completed:**
- Restored the existing `SignedTransaction` immutable artifact in `phantomx/signer.py`.
- Preserved the new `SignedChallenge`, `sign_challenge()`, `prove_signer_identity()`, and zero-key rejection controls.
- Committed as `148d9d01d0b6037312678d4af76ff1ade1a4e4e0`.

**Current verdict:** failure is understood and repaired. The signer-proof gate remains blocked until a fresh authoritative CI run proves the repaired implementation. This is exactly the fail-closed behavior we wanted from the certification pipeline.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** obtain fresh authoritative CI for `148d9d01...`; if GREEN, move to controlled production signer identity proof. If FAILURE, freeze and diagnose before any further gate progression.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
