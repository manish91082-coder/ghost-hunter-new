# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified software/project commit: `7f5a839bd5968961f23dff27b9dfa8da41539993`
- Latest repository-side procedure/test commit: `2caa8ff285fa98e061dc22da82502bff2765b812`
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
- Controlled private-relay evidence intake specification: `PHASE19_PRIVATE_RELAY_EVIDENCE_INTAKE.md`
- Controlled private-relay evidence validator: `scripts/validate_private_relay_evidence.py`
- Controlled private-relay evidence validator tests: `tests/phase19/test_private_relay_evidence_validator.py`
- Historical deployment-record forensic finding: an older commit `8460c589ef6b82b1da08d73624f29d0cd63d2549` contains `v2/v3` records asserting a Polygon Mainnet deployment at `0x24056bCA6538693aE94Cc97E82f21Ee4EC7f1286` with deployment tx `0x92bc4dc8b3450332c281445fb4443f8725586b18e880a063e0892af2c28c595a`; these records are historical repository claims only and are **NOT ACCEPTED** as current production-authority evidence because they lack the current controlled quorum/provenance contract and are not present as an accepted evidence package on the current canonical branch
- Production readiness decision: **NOT ACHIEVED**
- Controlled production signer identity: **BLOCKED**. No fresh externally held production-signer challenge signature and provenance record is present.
- Controlled production Polygon provider authority: **BLOCKED**. Repository-side observer, evidence contract, validator, tests, and controlled observation runbook are prepared and CI-certified, but no controlled production observation evidence from explicitly approved endpoints is present.
- Controlled production private relay: **BLOCKED**. HTTPS/private assertion/evidence tooling is now prepared and adversarially tested in the repository, but no approved production relay proof/evidence is present.
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

The private-relay boundary accepts only explicit HTTPS configuration with an explicit `private=true` assertion and no public fallback. Authentication material is sourced externally and is intentionally excluded from the evidence package and routine representation. The new evidence validator is offline-only and validates schema, HTTPS/private assertions, external authentication configuration assertion, prohibited material markers, provenance, and canonical evidence integrity.

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

Repository-side private-relay evidence intake, offline validation, and adversarial validator coverage have now been added. The current repository-side implementation is preparation only and does not constitute proof that any real production relay is approved or reachable.

The new validator intentionally refuses to accept non-HTTPS, non-private, missing-authentication, unknown-field, prohibited-material, provenance-missing, or tampered evidence packages.

## NEXT ATOMIC ACTION
Verify the new private-relay evidence validator through the Phase-19 CI workflow. If CI fails, repair only the failing boundary. If CI passes, proceed to a controlled external private-relay observation against an explicitly approved production private endpoint and retain only non-secret evidence. Keep signer, Polygon authority, shadow, realized-PnL, and live-capital gates locked.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
