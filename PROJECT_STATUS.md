# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified software/project commit: `7f5a839bd5968961f23dff27b9dfa8da41539993`
- Latest repository-side procedure commit: `fa63a0a7faf8e3f03b710deb3c4bb4b6b700b67f`
- Current Phase-19 CI certification: workflow run `442` / run ID `35065382193` **GREEN** on `7f5a839bd5968961f23dff27b9dfa8da41539993`; all primary steps passed: dependency install, Foundry install, Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and full Phase-19 unittest suite
- Prior completed Phase-19 CI certification: run `35018490583` / workflow run `439` **GREEN** on certified software commit `ebf794537c531a1241426a2bca9f355e205e44fc`
- Final executable implementation: `d018f8aea32d7db5aa012b02dcaacab87435af4c`
- Recovered-settlement certification `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Adapter adversarial certification `#423`: **GREEN**
- Durable quorum observation admission store: `9cd129c26c23b62d5ae0e7ea796f070fd7802c9c`
- Execution-observation quorum gate: `2a02e9110f303befa1fba2b0311f0e321530f0ba`
- Fresh certification `#427`: **GREEN**
- End-to-end quorum recovery isolation certification `#430`: **GREEN**
- Settlement reconciliation quorum boundary: `6a48ed044cc1579116b75e3f801e6fa866f2e89b`
- Quorum settlement reconciliation certification `#432`: **GREEN**
- Quorum recovery provenance boundary: `03e2c93ee8b1116d38b81332f45f84265b4a5c3d`
- Quorum recovery provenance certification `#435`: **GREEN**
- Final Phase-19 adversarial recovery/settlement matrix: `d018f8aea32d7db5aa012b02dcaacab87435af4c`
- Final matrix certification `#436`: **GREEN**
- Production-readiness audit certification `#437`: **GREEN**
- Controlled signer evidence intake specification: `PHASE19_SIGNER_EVIDENCE_INTAKE.md`
- Controlled signer evidence validator: `scripts/validate_signer_evidence.py` (`ebf794537c531a1241426a2bca9f355e205e44fc`)
- Controlled Polygon authority evidence intake specification: `PHASE19_PRODUCTION_AUTHORITY_EVIDENCE_INTAKE.md`
- Controlled Polygon authority observation runbook: `PHASE19_PRODUCTION_AUTHORITY_OBSERVATION_RUNBOOK.md`
- Controlled Polygon authority evidence validator: `scripts/validate_production_authority_evidence.py`
- Controlled Polygon authority validator tests: `tests/phase19/test_production_authority_evidence_validator.py`
- Production readiness decision: **NOT ACHIEVED**
- Controlled production signer identity: **BLOCKED**. No fresh externally held production-signer challenge signature and provenance record is present.
- Controlled production Polygon provider authority: **BLOCKED**. Repository-side observer, evidence contract, validator, tests, and controlled observation runbook are prepared and CI-certified, but no controlled production observation evidence from explicitly approved endpoints is present.
- Controlled production private relay: **BLOCKED**. Explicit HTTPS private-relay configuration is required and public fallback is forbidden, but no approved production relay proof/evidence is present.
- Controlled shadow/staging: **BLOCKED**. No independently evidenced production-like shadow/staging execution artifact using the identical immutable chain is present.
- Realized live PnL: **BLOCKED**. No controlled live-mainnet realized settlement evidence exists and live capital remains locked.
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## VERIFIED CAPABILITIES
Deterministic economics, immutable authorization/envelope binding, quote and simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, private-only submission, recovery, receipt reconciliation, executor controls, and authority quorum/provenance/freshness controls are implemented. #420, #423, #427, #430, #432, #435, #436, #437, and #442 provide certified repository-side gates.

The production chain observer is read-only and requires a unique quorum-backed decision.

The production authority module remains environment-driven and read-only, requiring explicit operator-supplied provider configuration and validating HTTPS endpoints, executor identity, and expected signer before authority observation.

The controlled authority evidence validator checks Polygon chain identity, common-block consistency, owner/signer binding, runtime-code identity, quorum membership, canonical evidence hash, and required provenance fields without network access, signing, submission, or broadcast.

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Controlled shadow/staging evidence using the identical immutable artifact chain.
5. Controlled realized live settlement/PnL evidence satisfying strict `net > $0.20` after all applicable costs.
6. Independent re-audit after all production gates are evidenced.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
Workflow run `442` / run ID `35065382193` is **GREEN**. The authority validator coverage and all earlier Phase-19 deterministic controls are CI-certified.

The next repository-side procedure is now documented in `PHASE19_PRODUCTION_AUTHORITY_OBSERVATION_RUNBOOK.md`. It defines the controlled, observation-only sequence: freeze approved inputs, validate HTTPS providers, prove chain 137, select a common block, observe owner and runtime code, require quorum agreement, verify owner-to-signer binding, construct the non-secret evidence package, run the offline validator, and obtain independent review.

This procedure is preparation only. It does not create production authority proof until actual observations from explicitly approved production endpoints are externally captured and independently reviewed.

## NEXT ATOMIC ACTION
Execute the controlled production Polygon authority observation procedure using explicitly approved production endpoints and the intended deployed executor. Capture only the required non-secret evidence package, then run `scripts/validate_production_authority_evidence.py` offline. If no approved production endpoints/executor/signer are available, keep the gate BLOCKED and do not substitute public/fork infrastructure. Keep signer, relay, shadow, realized-PnL, and live-capital gates locked.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
