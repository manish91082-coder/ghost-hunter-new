# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `e3040c24b8c5119a697847e7b3a4bfa01f8f2e5c`
- External signer verifier: `4c65e6e6520e6a5003182af2fc58abeb25f8c073`
- Signer identity operator CLI: `415d722e938650e869ba6d9bda450d35533c70ef`
- Signer identity CLI tests: `e3040c24b8c5119a697847e7b3a4bfa01f8f2e5c`
- Latest signer identity implementation: `fd34078fae864c02136484eeef3afd5f4a6c05a4`
- Latest signer artifact repair: `148d9d01d0b6037312678d4af76ff1ade1a4e4e0`
- Fresh authoritative repair CI: run `#349` GREEN for `148d9d01...`
- Fresh PR-head CI: run `#354` GREEN for `9489c047...`
- Fresh post-CLI CI: run `#357` GREEN for `e3040c24...`
- Certification PR: `#1` (OPEN, base `master`)
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, least-privilege/time-bounded CI execution, rejection of an all-zero signer private key, a non-secret signer identity challenge/proof boundary with cryptographic address recovery, restoration of the immutable signed-transaction artifact, an external verifier that can independently validate challenge signatures without private-key access, and an operator-safe CLI that generates fresh challenges and verifies externally returned signatures without private-key access.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

Fresh repair validation run `#349` tested `148d9d01...` and concluded **SUCCESS**. It completed Solidity compile, 14/14 EVM tests, 3/3 Polygon fork smoke tests, 1/1 Polygon fork execution probe, and the Python suite.

Fresh PR-head validation run `#354` tested `9489c047...` and concluded **SUCCESS**. The job completed every workflow stage. Evidence from the job log: 14/14 EVM tests passed, 3/3 Polygon fork smoke tests passed, 1/1 Polygon fork execution probe passed, and the Phase-19 Python suite ran **430 tests with 0 failures**, including all five new external signer identity verifier tests.

Fresh post-CLI validation run `#357` tested `e3040c24...` and concluded **SUCCESS**. The workflow job completed all stages successfully, including the Phase-19 Python suite. Its checked-in changes add the operator-safe signer identity CLI and five CLI safety/regression tests.

Run `#348` remains historical failure evidence: it tested `fd34078f...`, passed compile/EVM/Polygon stages, then failed in Python because `SignedTransaction` had been removed during signer-proof hardening. The deterministic regression was repaired in `148d9d01...`, and the repair is now GREEN.

Historical GREEN runs remain historical evidence only and do not substitute for current implementation proof.

## 5. CURRENT SIGNER IDENTITY GATE
The concrete signer exposes a non-secret cryptographic challenge proof. The external verifier accepts a fresh 32-byte challenge and a 65-byte signature, recovers the Ethereum address, requires an exact match with the expected address, and rebuilds the immutable evidence record. The verifier requires no signer object and no private-key access.

The operator CLI now provides a safe execution boundary: `--generate-challenge` creates a fresh 32-byte challenge, while verification accepts only the expected address, exact challenge, and externally produced 65-byte signature. A successful verification prints deterministic JSON evidence; a mismatch prints only a BLOCKED error and returns a non-zero code. No private-key argument exists.

The mechanism, independent verifier, and CLI are CI-certified. The **actual production signer identity gate remains NOT GREEN** because no actual production signer has yet supplied independently witnessed challenge evidence tied to the intended production address.

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
- Fresh current implementation CI: **GREEN** on `e3040c24...` via run `#357`.

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

**Atomic task completed:** built and CI-certified the operator-facing non-secret signer identity evidence utility.

**New evidence:**
- Run `#357` for `e3040c24...` is **SUCCESS**.
- All Phase-19 workflow stages completed successfully.
- The CLI generates fresh 32-byte challenges without key material and verifies externally supplied 65-byte signatures against an expected address.
- CLI regression coverage passed in the same authoritative suite.

**Current verdict:** the complete signer identity infrastructure is now CI-certified, including the signer, verifier, and operator-safe evidence boundary. Actual production signer control remains unproven and therefore blocked.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** execute the controlled production signer proof outside the repository using an externally held production signer: generate a fresh challenge, obtain exactly one signature over that challenge, independently verify the recovered address against the intended production signer address, and preserve the resulting evidence record. Do not expose or transmit private key material. After that, proceed to approved Polygon/provider authority evidence.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
