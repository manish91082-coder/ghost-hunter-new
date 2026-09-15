# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `6e2cef743f76c9af3c00a722cc147ee724996bd6`
- Authority freshness implementation: `ea4e74dfb9a034c96faa9cd242055263c90bce0f`
- Authority reuse policy: `6f7b329fcffe40fc81fee8d95779a8d9751450be`
- Latest coordinator freshness integration: `53c84152a3df0407b3d37eaf4fee3577481b8829`
- Latest signer freshness integration: `7b8314a11490921b02240b27175304aa1f6d3687`
- Latest submission fixture compatibility repair: `6e2cef743f76c9af3c00a722cc147ee724996bd6`
- Authority freshness tests: `76aa052b9b0087056d6b6da6aec924f89a507020`
- Coordinator freshness tests: `4bec83c21f85ca82e34bf86efb0f92a8f1d7ed3d`
- Signer freshness tests: `9a4fd321e1725d1abece2d689a26cec60e379bf7`
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
- Authority provenance certification: run `#376` GREEN
- Authority freshness/replay run `#377`: FAILED, preserved as implementation/test contract evidence
- Authority freshness implementation run `#378`: GREEN
- Replay-resistant reuse policy run `#379`: GREEN
- Reuse-boundary certification run `#380`: GREEN
- Coordinator freshness integration runs `#381/#382`: FAILED, superseded by minimal compatibility repair
- Signer freshness integration run `#383`: FAILED, exposed missing authority-hash assertion plus block-context semantics
- Coordinator/signing repair run `#384`: FAILED, superseded
- Latest combined certification run `#385`: FAILED with 477 Python tests, 3 failures and 58 errors; compile, EVM, Polygon smoke, and Polygon execution probe all passed
- Latest compatibility repair commit: `6e2cef743f76c9af3c00a722cc147ee724996bd6`
- Fresh CI for latest compatibility repair: **NOT YET OBSERVED**
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, pre-network blocking of repeated submission of an already-submitted durable artifact, explicit regression coverage that terminal `PROFIT_CONFIRMED`/`PROFIT_FAILED` states cannot be reopened by reorg recovery evidence, least-privilege/time-bounded CI execution, rejection of an all-zero signer private key, a non-secret signer identity challenge/proof boundary with cryptographic address recovery, restoration of the immutable signed-transaction artifact, an external verifier that can independently validate challenge signatures without private-key access, an operator-safe signer CLI, a controlled production signer identity runbook, a strict read-only Polygon HTTP transport with an allowlisted method surface and no transaction submission path, an environment-driven production Polygon authority assembly boundary that accepts only explicitly supplied HTTPS endpoints, quorum, executor address, and expected signer address and feeds the existing read-only quorum/owner binding layer, an operator-facing production authority audit CLI that emits only canonical non-secret authority evidence and fails closed without echoing endpoint/provider exception detail, static production-authority surface checks, authority evidence that cryptographically records the names of the providers that actually attested the winning owner/runtime-code observation, replay-resistant block-age freshness protection for authority evidence reuse, and freshness enforcement at both the execution-coordinator and signer boundaries.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow runs on branch pushes and pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, grants only `contents: read`, enforces a 30-minute job timeout, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

Fresh signer repair validation run `#349` tested `148d9d01...` and concluded **SUCCESS**.

Fresh signer-runbook validation run `#360` tested `1c76ab9...` and concluded **SUCCESS**.

Fresh Polygon transport validation run `#364` tested `04bcaf9...` and concluded **SUCCESS**, including 435/435 Python tests.

Run `#367` tested the production-authority assembly tests and concluded **SUCCESS**, with all workflow stages green and the authoritative log recording 453 tests, 0 failures.

Run `#371` validated the corrected fail-closed operator authority CLI and completed successfully.

Runs `#373` and `#374` certified the provider-provenance implementation/test contract. Run `#375` exposed a real contract mismatch. Run `#376` then completed successfully for the provenance output certification layer.

User-supplied GitHub Actions evidence shows freshness sequence runs `#377` failed, then `#378`, `#379`, and `#380` completed successfully.

Runs `#381` and `#382` exposed the compatibility impact of making coordinator authority reuse policy explicit. Run `#383` exposed signer-boundary semantic gaps: the signer path had dropped the explicit governor authority-hash equality assertion and was evaluating freshness against the wrong block context for coordinator-created authority observations. Run `#384` remained failed. Latest combined run `#385` demonstrated the remaining concrete failures: 58 fixture/setup errors because shared submission fixtures had not yet supplied the new required coordinator policy, plus three signer assertion failures. The authoritative run metadata shows compile, 14/14 EVM, 3/3 Polygon fork smoke, and 1/1 Polygon fork execution probe succeeded; only the Python stage failed. fileciteturn973file0L2-L2

The current repair path binds the shared submission fixture to an explicit `AuthorityEvidenceReusePolicy`, preserves the explicit policy requirement rather than introducing an unsafe implicit coordinator default, and keeps coordinator/signer freshness checks on the correct proven block boundaries.

Fresh CI for the latest compatibility repair `6e2cef743f76c9af3c00a722cc147ee724996bd6` has not yet been observed. No GREEN claim is made.

Historical GREEN runs remain historical evidence only and do not substitute for current implementation proof.

## 5. CURRENT SIGNER IDENTITY GATE
The signer exposes a non-secret cryptographic challenge proof. The external verifier accepts a fresh 32-byte challenge and a 65-byte signature, recovers the Ethereum address, requires an exact match with the expected address, and rebuilds the immutable evidence record. The verifier requires no signer object and no private-key access.

The operator CLI generates fresh challenges and verifies externally produced signatures. The checked-in runbook defines the controlled production procedure, acceptance criteria, provenance requirements, and fail-closed handling. The mechanism is CI-certified. The **actual production signer identity gate remains NOT GREEN** until real externally held production-signer evidence is supplied and independently verified.

The signing boundary now explicitly requires Governor authority-hash equality and a bounded authority-evidence reuse window. Coordinator-created signing passes the current observation block separately from the Governor's proven simulation block, while requiring the authority observation not to predate that proven block. fileciteturn971file0L7-L11

## 6. CURRENT POLYGON RPC / AUTHORITY GATE
`phantomx/polygon_rpc.py` is the fail-closed read policy boundary: Polygon chain 137 is mandatory, provider identity is explicit, and quorum disagreement fails closed. `phantomx/polygon_rpc_http.py` is CI-certified as a separate network transport. It permits only read methods needed by the Phase-19 observation path; write/submission methods and unknown methods are blocked before network I/O.

`phantomx/production_authority.py` converts explicitly supplied operator configuration into the existing read-only provider and executor-authority quorum layers. It contains no provider defaults, no private keys, no signing, and no transaction submission/broadcast capability. Production endpoints are required to be HTTPS and cannot contain embedded credentials. The associated assembly tests are CI-certified by run `#367`.

`scripts/observe_production_authority.py` is the operator-facing controlled observation boundary. It consumes the approved environment configuration, performs the existing read-only quorum/owner verification path, and emits only schema version, Polygon chain ID, executor, owner, observed block, runtime code hash, attesting provider names, and evidence hash. Endpoint values, credential-bearing configuration, timeouts, private keys, submission flags, and transport exception details are not emitted. The CLI surface is additionally covered by the static source audit committed in `dadd4c5b...`.

`ExecutorAuthorityEvidence` records the provider names that attested the winning owner/runtime-code result. These names are included in the canonical evidence digest, so changing the attesting set changes evidence identity. Runtime code binding deliberately excludes provider names because it represents the deployed owner/code identity independent of transport provenance.

`verify_executor_authority_freshness` rejects authority evidence from the future and evidence older than the explicit maximum block-age window. `AuthorityEvidenceReusePolicy` and `verify_reusable_production_authority_evidence` combine exact executor/signer binding with that freshness check and collapse reuse failures to a generic blocked outcome. fileciteturn954file0L7-L11

The execution coordinator invokes this reusable authority boundary before nonce reservation with the proven simulation block as the lower bound, and propagates the explicit policy to signing. The signer rechecks the same authority hash and evaluates freshness against the current signing observation block while enforcing the Governor block as the minimum acceptable observation. fileciteturn972file0L7-L11 fileciteturn971file0L7-L11

This is **configuration/orchestration/CLI/static-surface/provenance/freshness implementation certification, not production authority certification**. The actual P0 authority gate still requires real explicitly approved provider endpoints, a confirmed intended deployed executor address, the expected signer address, fresh multi-provider quorum evidence against that exact executor, and controlled provenance of the observing environment.

## 7. CURRENT BLOCKERS / P0 GATES
1. **Controlled production signer identity proof** without exposing private key material.
2. **Controlled production Polygon network/provider authority proof** using explicitly approved production endpoints and the deployed executor address.
3. **Production private relay capability** with no public fallback.
4. **Startup/recovery safety under production-like conditions**, including a production-grade settlement reorg policy.
5. **Controlled shadow/staging evidence** using the identical immutable artifact chain.
6. **Final realized live PnL evidence** after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, expected signer address, fresh authority evidence with attesting-provider provenance, explicit evidence-reuse age policy, controlled evidence retention, and fresh CI certification of every newly modified execution/signer consumer.

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
- Provider-provenance implementation/test layer: **GREEN** through run `#376`.
- Authority freshness/replay protection: **GREEN** through user-observed runs `#378`, `#379`, `#380`.
- Coordinator/signer freshness consumer integration: **implemented; latest fresh CI pending after compatibility repair**.

### B. First real-life hunt readiness
- Fresh current implementation CI GREEN: **NO, not yet established for latest compatibility repair**.
- Production-control gates GREEN: **0 / 5**.
- First real-money hunt: **NOT READY**.

### C. Continuous hunting readiness
- Verified live cycles: **0**.
- Continuous hunting: **NOT ACHIEVED**.

## 10. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task completed:** acted on the user-supplied CI failure evidence from runs `#381` through `#385`, traced the exact dominant failures to an explicit coordinator policy compatibility break and signer-boundary authority semantics, repaired the reusable authority helper to accept the proven lower block bound, restored explicit Governor authority-hash equality at signing, propagated current block context through the coordinator-to-signer path, and updated the shared submission fixture to supply the explicit reuse policy.

**New evidence:**
- User-observed freshness certification: `#378`, `#379`, `#380` GREEN.
- Latest combined failure: `#385`, 477 tests, 3 failures, 58 errors, with compile/EVM/Polygon stages passing. fileciteturn973file0L2-L2
- Production authority reuse helper repair: `8a6c3c44...`.
- Signer boundary repair: `7b8314a1...`.
- Coordinator boundary repair: `53c84152...`.
- Submission fixture compatibility repair: `6e2cef74...`.

**Current verdict:** authority evidence freshness is enforced at the reusable-evidence layer, execution coordinator, and signer boundary. The latest CI failure has been reduced to a concrete compatibility contract repair; that newest repair still requires fresh CI before certification can be advanced.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** certify `6e2cef743f76c9af3c00a722cc147ee724996bd6` in fresh CI. If any failures remain, isolate the smallest contract mismatch, repair minimally, and repeat. Once GREEN, perform the repository-wide alternate-path audit for authority/signing bypasses.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
