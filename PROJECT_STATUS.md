# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified software/project commit: `eea845af1388ea619c54ffc4faf8a34d215e2aa1`
- Latest repository-side procedure/launch worksheet commit: `c755539dd5f22e85deace15e8196089119aa783f`
- Current Phase-19 CI certification: workflow run `456` / run ID `35074699670` **GREEN** on `eea845af1388ea619c54ffc4faf8a34d215e2aa1`; dependency install, Foundry install, Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and full Phase-19 unittest suite all passed
- Previous Phase-19 CI certification: workflow run `451` / run ID `35070288544` **GREEN** on `7506b41c1e7ec876b39ae8428896c374a48b0181`
- Previous Phase-19 CI certification: workflow run `446` / run ID `35067167421` **GREEN** on `2caa8ff285fa98e061dc22da82502bff2765b812`
- Previous Phase-19 CI certification: workflow run `442` / run ID `35065382193` **GREEN** on `7f5a839bd5968961f23dff27b9dfa8da41539993`
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
- Accelerated parallel gate plan: `PHASE19_ACCELERATED_GATE_PLAN.md`
- Consolidated external evidence session protocol: `PHASE19_CONSOLIDATED_EXTERNAL_EVIDENCE_SESSION.md`
- Consolidated external evidence session coordinator: `scripts/validate_consolidated_evidence_session.py`
- Consolidated external evidence session coordinator tests: `tests/phase19/test_consolidated_evidence_session_validator.py`
- External gate launch packet: `PHASE19_EXTERNAL_GATE_LAUNCH_PACKET.md`
- One-shot external gate session worksheet: `PHASE19_OPERATOR_ONE_SHOT_SESSION.md` (frozen to verified artifact `eea845af...`)
- Shadow/staging evidence validator: `scripts/validate_shadow_staging_evidence.py`
- Shadow/staging evidence validator tests: `tests/phase19/test_shadow_staging_evidence_validator.py`
- Historical deployment-record forensic finding: older commit `8460c589ef6b82b1da08d73624f29d0cd63d2549` contains `v2/v3` records asserting a Polygon Mainnet deployment at `0x24056bCA6538693aE94Cc97E82f21Ee4EC7f1286` with deployment tx `0x92bc4dc8b3450332c281445fb4443f8725586b18e880a063e0892af2c28c595a`; these are historical repository claims only and are not accepted as current production-authority evidence
- Production readiness decision: **NOT ACHIEVED**
- Controlled production signer identity: **BLOCKED**. No fresh externally held production-signer challenge signature and provenance record is present.
- Controlled production Polygon provider authority: **BLOCKED**. Repository-side observer, evidence contract, validator, tests, and runbook are prepared and CI-certified, but no controlled production observation evidence from explicitly approved endpoints is present.
- Controlled production private relay: **BLOCKED**. HTTPS/private assertion/evidence tooling and adversarial validation are CI-certified, but no approved production relay observation evidence is present.
- Controlled shadow/staging: **BLOCKED**. A dedicated offline validator is prepared for an exact frozen-artifact shadow/staging record, but no independently evidenced staging execution artifact is present.
- Realized live PnL: **BLOCKED**. No controlled live-mainnet realized settlement evidence exists and live capital remains locked.
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## ACCELERATION MODE
Independent production-evidence lanes are processed as parallel workstreams instead of serial micro-steps. Repository-safe preparation, CI verification, forensic review, and evidence packaging advance concurrently. Evidence-dependent gate promotion remains independently serialized.

Current parallel lanes:
- A: Polygon production authority evidence
- B: production signer identity evidence
- C: private-relay evidence
- D: identical-artifact shadow/staging evidence
- E: realized economics/PnL evidence

A single consolidated controlled external evidence session should capture every currently satisfiable lane. No secrets are combined into the evidence bundle.

## CURRENT EXTERNAL INFRASTRUCTURE RESEARCH
- Polygon Labs' April 2, 2026 launch post states Polygon Private Mempool is live and provides a private transaction-submission path that bypasses the public mempool, with a stated free tier. citeturn700408search2
- Polygon's current Private Mempool access page is still presented as a request-access flow. citeturn700408search1
- Polygon's August 24, 2026 follow-up again states Private Mempool is live and describes a private submission path, while also describing partner availability through bloXroute. citeturn700408search3
- These sources create an intentional project-level distinction: vendor/platform availability is research evidence, while project approval/authentication is an external controlled fact that must be captured separately before any production gate is promoted.
- Polygon support guidance also distinguishes public RPC from private provider options and identifies private providers such as Infura, Alchemy, and QuickNode as possible RPC sources, while not endorsing a single provider. citeturn700408search4

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## VERIFIED CAPABILITIES
Deterministic economics, immutable authorization/envelope binding, quote and simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, private-only submission, recovery, receipt reconciliation, executor controls, and authority quorum/provenance/freshness controls are implemented. #420, #423, #427, #430, #432, #435, #436, #437, #446, and #451 provide certified repository-side gates.

The production chain observer is read-only and requires a unique quorum-backed decision.

The production authority module remains environment-driven and read-only, requiring explicit operator-supplied provider configuration and validating HTTPS endpoints, executor identity, and expected signer before authority observation.

The controlled authority evidence validator checks Polygon chain identity, common-block consistency, owner/signer binding, runtime-code identity, quorum membership, canonical evidence hash, and required provenance fields without network access, signing, submission, or broadcast.

The private-relay boundary accepts only explicit HTTPS configuration with an explicit `private=true` assertion and no public fallback. Authentication material is sourced externally and is intentionally excluded from the evidence package and routine representation. The private-relay evidence validator is offline-only and validates schema, HTTPS/private assertions, external authentication configuration assertion, prohibited material markers, provenance, and canonical evidence integrity.

The consolidated session coordinator validates the session manifest structure and invokes only existing offline lane validators for evidence files that are actually present. Missing evidence remains BLOCKED; one lane cannot infer GREEN for another.

The external gate launch packet and one-shot session worksheet compress signer, Polygon authority, private relay, and identical-artifact shadow/staging preparation into one controlled session while keeping realized PnL as a separately controlled settlement gate.

The shadow/staging validator is offline-only and checks exact artifact identity, EVM identities, route/economic/authority/submission-policy proof identities, staging environment identity, operator/witness provenance, explicit `SHADOW_STAGING` mode, `live_capital=false`, `broadcast=false`, allowed outcome, and canonical evidence hash. It never contacts production or authorizes execution.

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Controlled shadow/staging evidence using the identical immutable artifact chain.
5. Controlled realized live settlement/PnL evidence satisfying strict `net > $0.20` after all applicable costs.
6. Independent re-audit after all production gates are evidenced.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
Workflow run `456` / run ID `35074699670` completed **GREEN** on frozen artifact `eea845af1388ea619c54ffc4faf8a34d215e2aa1`. The complete Phase-19 deterministic pipeline passed dependency setup, Foundry setup, Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full Phase-19 unittest suite. This certifies the repository-side shadow/staging validator and consolidated coordinator integration on that artifact. fileciteturn231file0

A documentation consistency audit found the one-shot external worksheet still pointed at the superseded `7506b41...` anchor; that drift was corrected and committed as `c755539dd5f22e85deace15e8196089119aa783f`, with the worksheet now explicitly frozen to `eea845af...`. fileciteturn239file0

The shadow/staging lane is repository-ready at the offline-validation boundary, but no independently evidenced staging execution artifact exists yet. No production gate has been promoted from repository tests, historical deployment claims, public/fork observations, vendor availability, or estimated economics.

## NEXT ATOMIC ACTION
Proceed directly to the single controlled external-evidence session for A/B/C/D using the frozen artifact `eea845af1388ea619c54ffc4faf8a34d215e2aa1` and the updated one-shot worksheet. Capture only externally controlled, non-secret evidence records, then run the consolidated offline coordinator and independent review. Keep realized-PnL, live signing, public broadcast, and live-capital locks intact until their own acceptance chains are complete.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**