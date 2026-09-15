# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest signer identity implementation commit: `fd34078fae864c02136484eeef3afd5f4a6c05a4`
- Latest authoritative GREEN CI for implementation: run `#345` on `919e72cf6099ccb4fc5f6ff8ac1151bd5ec51c8f`
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, least-privilege/time-bounded CI execution, rejection of an all-zero signer private key, and a non-secret signer identity challenge/proof boundary with cryptographic address recovery.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

Authoritative run `#345` tested signer-hardening commit `919e72cf6099ccb4fc5f6ff8ac1151bd5ec51c8f` and concluded **SUCCESS**: Solidity compile successful; **14/14 EVM**, **3/3 Polygon fork smoke**, **1/1 Polygon fork execution probe**, and **422/422 Python tests**, with **0 failures and 0 skips**. The subsequent signer-test syntax repair and identity-proof implementation are newer implementation commits and therefore require their own fresh CI certification before being considered certified.

## 5. CURRENT SIGNER IDENTITY GATE
The concrete signer now exposes a non-secret cryptographic challenge proof: an external verifier can supply a fresh 32-byte challenge, receive only a 65-byte signature, recover the Ethereum address, and compare it with the expected production signer address. The private key itself remains inside the signer and is never placed in the repository, logs, or chat.

The gate is **not GREEN yet**. We have implemented the proof mechanism and regression tests, but we do not yet have controlled evidence from the actual intended production signer address/key. A test private key is not production identity evidence.

## 6. CURRENT BLOCKERS / P0 GATES
1. **Fresh CI certification of the signer identity-proof implementation**.
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
- Latest authoritative implementation certification: **GREEN for commit `919e72cf...`**.
- Newer signer identity-proof implementation: **awaiting fresh CI**.

### B. First real-life hunt readiness
Required pre-hunt controls are fresh CI for the current implementation, controlled production signer identity, approved Polygon/provider authority, private relay, production-like recovery/reorg, and identical-artifact shadow/staging evidence.
- Fresh current-implementation CI GREEN: **NO**.
- Production-control gates GREEN: **0 / 5** after current CI.
- First real-money hunt: **NOT READY**.

### C. Continuous hunting readiness
- Verified live cycles: **0**.
- Continuous hunting: **NOT ACHIEVED**.

## 9. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** signer identity proof mechanism added without disclosing key material.

**New work completed:**
- Extended the concrete Ethereum signer with `sign_challenge()` for offline cryptographic key-control evidence.
- Added `prove_signer_identity()` which validates a fresh 32-byte challenge, recovers the signer address from the returned signature, and produces immutable evidence hashes.
- Added regressions for valid proof, blind-signer proof, and wrong-signer rejection.
- Corrected the test file syntax and kept the zero-key regression.
- No production key or production address was introduced.

**Certification state:** previous implementation state is GREEN by authoritative run #345, but the newer signer identity-proof implementation is **UNCERTIFIED until its own CI run is GREEN**.

**Current verdict:** the production signer gate is now technically instrumented for safe proof, but it is not yet externally evidenced for the real production signer. The next action is fresh CI; after that, controlled production signer identity evidence.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** obtain fresh authoritative CI for the current signer-proof implementation; on GREEN, execute the controlled production signer identity proof protocol without exposing private key material.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
