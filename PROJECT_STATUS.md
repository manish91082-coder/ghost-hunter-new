# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `04bcaf9261e1c61e13bbe621adf04f5bd3aa7d09`
- Polygon RPC HTTP transport: `4a8e8338884f2bc63002d71d3e9984d07bdfd427`
- Polygon RPC HTTP tests: `04bcaf9261e1c61e13bbe621adf04f5bd3aa7d09`
- External signer verifier: `4c65e6e6520e6a5003182af2fc58abeb25f8c073`
- Signer identity operator CLI: `415d722e938650e869ba6d9bda450d35533c70ef`
- Signer identity runbook: `1c76ab9da90d3c20785ae85ce14eeee29f6f8264`
- Latest signer identity implementation: `fd34078fae864c02136484eeef3afd5f4a6c05a4`
- Latest signer artifact repair: `148d9d01d0b6037312678d4af76ff1ade1a4e4e0`
- Fresh authoritative repair CI: run `#349` GREEN
- Fresh PR-head CI: run `#354` GREEN
- Fresh post-CLI CI: run `#357` GREEN
- Fresh signer-runbook CI: run `#360` GREEN
- Fresh Polygon transport CI: run `#364` GREEN for `04bcaf9...`
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, least-privilege/time-bounded CI execution, rejection of an all-zero signer private key, a non-secret signer identity challenge/proof boundary with cryptographic address recovery, restoration of the immutable signed-transaction artifact, an external verifier that can independently validate challenge signatures without private-key access, an operator-safe CLI, a controlled production signer identity runbook, and a strict read-only Polygon HTTP transport with an allowlisted method surface and no transaction submission path.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

Fresh repair validation run `#349` tested `148d9d01...` and concluded **SUCCESS**.

Fresh PR-head validation run `#354` tested `9489c047...` and concluded **SUCCESS**.

Fresh post-CLI validation run `#357` tested `e3040c24...` and concluded **SUCCESS**.

Fresh signer-runbook validation run `#360` tested `1c76ab9...` and concluded **SUCCESS**. The authoritative job log recorded **435 Python tests with 0 failures**, alongside successful compile, 14/14 EVM, 3/3 Polygon fork smoke, and 1/1 Polygon fork execution probe stages.

Fresh Polygon transport validation run `#364` tested `04bcaf9...` and concluded **SUCCESS**. The dedicated workflow job completed every stage successfully. Its authoritative job record confirms compile, EVM integration, Polygon fork smoke, Polygon fork execution probe, and the Phase-19 Python suite all completed with success. The detailed log also recorded the full Phase-19 suite as **435 tests, 0 failures**.

Run `#348` remains historical failure evidence: `fd34078f...` failed in Python because `SignedTransaction` had been removed during signer-proof hardening. The deterministic regression was repaired in `148d9d01...`, and that repair is GREEN.

Historical GREEN runs remain historical evidence only and do not substitute for current implementation proof.

## 5. CURRENT SIGNER IDENTITY GATE
The signer exposes a non-secret cryptographic challenge proof. The external verifier accepts a fresh 32-byte challenge and a 65-byte signature, recovers the Ethereum address, requires an exact match with the expected address, and rebuilds the immutable evidence record. The verifier requires no signer object and no private-key access.

The operator CLI generates fresh challenges and verifies externally produced signatures. The checked-in runbook defines the controlled production procedure, acceptance criteria, provenance requirements, and fail-closed handling. The mechanism is CI-certified. The **actual production signer identity gate remains NOT GREEN** until real externally held production-signer evidence is supplied and independently verified.

## 6. CURRENT POLYGON RPC / AUTHORITY GATE
`phantomx/polygon_rpc.py` is the fail-closed read policy boundary: Polygon chain 137 is mandatory, provider identity is explicit, and quorum disagreement fails closed. `phantomx/polygon_rpc_http.py` is now CI-certified as a separate network transport. It permits only `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getTransactionCount`, `eth_getCode`, and `eth_call`. Write/submission methods and unknown methods are blocked before network I/O; HTTP/JSON/response-id/endpoint validation also fails closed.

The transport certification is **not** production authority certification. The actual P0 authority gate still requires a controlled list of explicitly approved provider endpoints, a confirmed intended deployed executor address, and reproducible multi-provider quorum evidence gathered against that exact executor.

## 7. CURRENT BLOCKERS / P0 GATES
1. **Controlled production signer identity proof** without exposing private key material.
2. **Controlled production Polygon network/provider authority proof** using explicitly approved production endpoints and the deployed executor address.
3. **Production private relay capability** with no public fallback.
4. **Startup/recovery safety under production-like conditions**, including a production-grade settlement reorg policy.
5. **Controlled shadow/staging evidence** using the identical immutable artifact chain.
6. **Final realized live PnL evidence** after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, logs, and chat.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. DISTANCE-TO-GOAL SCORECARD
These are explicit planning metrics, not claims of external evidence.

### A. Engineering foundation
- Deterministic Phase-19 execution-integrity implementation: **substantially built**.
- Practical assessment: **~85% engineering foundation complete**.
- Latest signer/runbook implementation CI: **GREEN** through run `#360`.
- Polygon HTTP transport: **GREEN** through run `#364`.

### B. First real-life hunt readiness
- Fresh current implementation CI GREEN: **YES**.
- Production-control gates GREEN: **0 / 5**.
- First real-money hunt: **NOT READY**.

### C. Continuous hunting readiness
- Verified live cycles: **0**.
- Continuous hunting: **NOT ACHIEVED**.

## 10. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** introduced and certified the strict read-only Polygon HTTP transport boundary required to move from pure policy tests toward controlled provider-authority integration.

**New evidence:**
- Transport implementation: `4a8e8338...`.
- Transport tests/current implementation: `04bcaf92...`.
- Run `#360`: **SUCCESS** for signer runbook `1c76ab9...`.
- Run `#364`: **SUCCESS** for Polygon transport `04bcaf9...`.
- Run `#364` completed all workflow stages successfully; Phase-19 Python suite: **435/435**.

**Current verdict:** CI-certified signer identity infrastructure and CI-certified read-only Polygon HTTP transport are in place. Actual production signer identity and production Polygon/provider authority remain unproven and therefore blocked.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** perform controlled production Polygon/provider authority observation using explicitly approved endpoints and the intended deployed executor address. This must remain read-only and evidence-producing. Do not introduce submission-capable transport or use unapproved public endpoints as production authority evidence.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
