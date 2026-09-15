# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `76aa052b9b0087056d6b6da6aec924f89a507020`
- Latest authority freshness implementation: `ea4e74dfb9a034c96faa9cd242055263c90bce0f`
- Latest authority freshness tests: `76aa052b9b0087056d6b6da6aec924f89a507020`
- Production Polygon authority assembly: `2492cd97c750bc3aa37b30d25e9bc9fcb2fb0864`
- Production Polygon authority tests: `007789cabaa56b089ee89890b05596b7a1c18095`
- Production authority operator audit CLI: `f02e6db75ca27a061372f956defbee90f2de0d97`
- Production authority operator audit CLI tests: `374bdff9dc294dfd9c8869964ee16a2a4307d9b3`
- Production authority static surface audit: `dadd4c5b11261220f4b5bc17f7ce0d2f523d6721`
- Polygon RPC HTTP transport: `4a8e8338884f2bc63002d71d3e9984d07bdfd427`
- Polygon RPC HTTP tests: `04bcaf9261e1c61e13bbe621adf04f5bd3aa7d09`
- External signer verifier: `4c65e6e6520e6a5003182af2fc58abeb25f8c073`
- Signer identity operator CLI: `415d722e938650e869ba6d9bda450d35533c70ef`
- Signer identity runbook: `1c76ab9da90d3c20785ae85ce14eeee29f6f8264`
- Latest signer identity implementation: `fd34078fae864c02136484eeef3afd5f4a6c05a4`
- Latest signer artifact repair: `148d9d01d0b6037312678d4af76ff1ade1a4e4e0`
- Fresh authoritative repair CI: run `#349` GREEN
- Fresh signer-runbook CI: run `#360` GREEN
- Fresh Polygon transport CI: run `#364` GREEN
- Production-authority assembly test CI: run `#367` GREEN
- Production-authority CLI corrected boundary: run `#371` GREEN
- Authority provenance implementation CI: run `#373` GREEN
- Authority provenance certification: run `#376` GREEN for `fc0a1600...`
- Authority provenance first implementation run `#375`: FAILED and superseded
- Authority freshness/replay hardening: `ea4e74df...` implementation + `76aa052b...` tests; fresh CI pending
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, least-privilege/time-bounded CI execution, rejection of an all-zero signer private key, a non-secret signer identity challenge/proof boundary with cryptographic address recovery, restoration of the immutable signed-transaction artifact, an external verifier that can independently validate challenge signatures without private-key access, an operator-safe signer CLI, a controlled production signer identity runbook, a strict read-only Polygon HTTP transport with an allowlisted method surface and no transaction submission path, an environment-driven production Polygon authority assembly boundary that accepts only explicitly supplied HTTPS endpoints, quorum, executor address, and expected signer address and feeds the existing read-only quorum/owner binding layer, an operator-facing production authority audit CLI that emits only canonical non-secret authority evidence and fails closed without echoing endpoint/provider exception detail, static production-authority surface checks, authority evidence that cryptographically records the names of the providers that actually attested the winning owner/runtime-code observation, and replay-resistant block-age freshness protection for authority evidence reuse.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

Fresh signer repair validation run `#349` tested `148d9d01...` and concluded **SUCCESS**.

Fresh signer-runbook validation run `#360` tested `1c76ab9...` and concluded **SUCCESS**.

Fresh Polygon transport validation run `#364` tested `04bcaf9...` and concluded **SUCCESS**, including 435/435 Python tests.

Run `#367` tested `007789ca...` and concluded **SUCCESS**, with all workflow stages green and the authoritative log recording **453 tests, 0 failures**.

Run `#368` validated the initial production authority CLI. Run `#369` exposed a genuine runtime exception path. Run `#370` was an intermediate failed correction. Run `#371` validated the corrected fail-closed CLI boundary on `374bdff9...`.

Run `#373` validated the provider-provenance implementation. Run `#374` validated the provenance test contract. Run `#375` exposed a genuine implementation/test mismatch. Run `#376` then completed successfully for `fc0a1600...`, certifying the provenance output layer.

The newest authority freshness/replay hardening is implemented but fresh CI has not yet been observed. No GREEN claim is made for `ea4e74df...` / `76aa052b...` yet.

Historical GREEN runs remain historical evidence only and do not substitute for current implementation proof.

## 5. CURRENT SIGNER IDENTITY GATE
The signer exposes a non-secret cryptographic challenge proof. The external verifier accepts a fresh 32-byte challenge and a 65-byte signature, recovers the Ethereum address, requires an exact match with the expected address, and rebuilds the immutable evidence record. The verifier requires no signer object and no private-key access.

The operator CLI generates fresh challenges and verifies externally produced signatures. The checked-in runbook defines the controlled production procedure, acceptance criteria, provenance requirements, and fail-closed handling. The mechanism is CI-certified. The **actual production signer identity gate remains NOT GREEN** until real externally held production-signer evidence is supplied and independently verified.

## 6. CURRENT POLYGON RPC / AUTHORITY GATE
`phantomx/polygon_rpc.py` is the fail-closed read policy boundary: Polygon chain 137 is mandatory, provider identity is explicit, and quorum disagreement fails closed. `phantomx/polygon_rpc_http.py` is CI-certified as a separate network transport. It permits only read methods needed by the Phase-19 observation path; write/submission methods and unknown methods are blocked before network I/O.

`phantomx/production_authority.py` converts explicitly supplied operator configuration into the existing read-only provider and executor-authority quorum layers. It contains no provider defaults, no private keys, no signing, and no transaction submission/broadcast capability. Production endpoints are required to be HTTPS and cannot contain embedded credentials. The associated assembly tests are CI-certified by run `#367`.

`scripts/observe_production_authority.py` is the operator-facing controlled observation boundary. It consumes the approved environment configuration, performs the existing read-only quorum/owner verification path, and emits only schema version, Polygon chain ID, executor, owner, observed block, runtime code hash, attesting provider names, and evidence hash. Endpoint values, credential-bearing configuration, timeouts, private keys, submission flags, and transport exception details are not emitted. The CLI surface is additionally covered by the static source audit committed in `dadd4c5b...`.

`ExecutorAuthorityEvidence` records the provider names that attested the winning owner/runtime-code result. These names are included in the canonical evidence digest, so changing the attesting set changes evidence identity. Runtime code binding deliberately excludes provider names because it represents the deployed owner/code identity independent of transport provenance.

`verify_executor_authority_freshness` rejects authority evidence from the future and evidence older than the explicit maximum block-age window. `AuthorityEvidenceReusePolicy` and `verify_reusable_production_authority_evidence` combine exact executor/signer binding with that freshness check and collapse reuse failures to a generic blocked outcome.

This is **configuration/orchestration/CLI/static-surface/provenance/freshness implementation certification, not production authority certification**. The actual P0 authority gate still requires real explicitly approved provider endpoints, a confirmed intended deployed executor address, the expected signer address, fresh multi-provider quorum evidence against that exact executor, and controlled provenance of the observing environment.

## 7. CURRENT BLOCKERS / P0 GATES
1. **Controlled production signer identity proof** without exposing private key material.
2. **Controlled production Polygon network/provider authority proof** using explicitly approved production endpoints and the deployed executor address.
3. **Production private relay capability** with no public fallback.
4. **Startup/recovery safety under production-like conditions**, including a production-grade settlement reorg policy.
5. **Controlled shadow/staging evidence** using the identical immutable artifact chain.
6. **Final realized live PnL evidence** after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, expected signer address, fresh authority evidence with attesting-provider provenance, explicit evidence-reuse age policy, and controlled evidence retention. Private key material stays outside repository code, fixtures, logs, and chat.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. DISTANCE-TO-GOAL SCORECARD
These are explicit planning metrics, not claims of external evidence.

### A. Engineering foundation
- Deterministic Phase-19 execution-integrity implementation: **substantially built**.
- Practical assessment: **~85% engineering foundation complete**.
- Latest signer/runbook implementation CI: **GREEN** through run `#360`.
- Polygon HTTP transport: **GREEN** through run `#364`.
- Production authority assembly/test layer: **GREEN** through run `#367`.
- Operator authority observation CLI: **GREEN** through run `#371`.
- Provider-provenance implementation/test layer: **GREEN** through run `#376` for the tested commits.
- Authority freshness/replay protection: **implemented; fresh CI pending**.

### B. First real-life hunt readiness
- Fresh current implementation CI GREEN: **NO, not yet established for the latest freshness hardening**.
- Production-control gates GREEN: **0 / 5**.
- First real-money hunt: **NOT READY**.

### C. Continuous hunting readiness
- Verified live cycles: **0**.
- Continuous hunting: **NOT ACHIEVED**.

## 10. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** added replay-resistant authority-evidence reuse protection based on the observed Polygon block. Evidence is now rejectable when it is from the future or exceeds the configured maximum block-age window, and the production-specific reuse helper requires exact executor/signer binding plus freshness validation.

**New evidence:**
- Authority freshness implementation: `ea4e74df...`.
- Authority freshness tests: `76aa052b...`.
- User-supplied CI evidence: run `#376` GREEN for `fc0a1600...`.
- Fresh CI for the newest freshness hardening: **NOT YET OBSERVED**.

**Current verdict:** provider provenance is CI-certified through user-observed run `#376`. Freshness/replay protection is implemented but awaits fresh CI certification. Actual production signer identity and actual production Polygon/provider authority remain unproven and therefore blocked.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** obtain fresh CI certification for `ea4e74df...` / `76aa052...`; if GREEN, perform a deterministic replay/retention audit across authority evidence consumers and ensure every production reuse path requires an explicit freshness check before execution authorization.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
