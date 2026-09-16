# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified software/project commit: `7f5a839bd5968961f23dff27b9dfa8da41539993`
- Current Phase-19 CI: workflow run `442` / run ID `35065382193` **IN PROGRESS** on `7f5a839bd5968961f23dff27b9dfa8da41539993`; completed so far: dependency install, Foundry install, Solidity compilation, EVM integration, Polygon fork protocol smoke; Polygon fork execution probe is in progress and unittest suite has not started
- Latest completed Phase-19 CI certification: run `35018490583` / workflow run `439` **GREEN** on certified software commit `ebf794537c531a1241426a2bca9f355e205e44fc`
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
- Final matrix certification `#436`: **GREEN**. The hardened final matrix workflow completed successfully across Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full Phase-19 unittest suite.
- Production-readiness gate audit: `PHASE19_PRODUCTION_READINESS_AUDIT.md`
- Production-readiness audit certification `#437`: **GREEN**. The audit record was committed and the complete Phase-19 workflow passed on the audit commit.
- Controlled signer evidence intake specification: `PHASE19_SIGNER_EVIDENCE_INTAKE.md`
- Controlled signer evidence validator: `scripts/validate_signer_evidence.py` (`ebf794537c531a1241426a2bca9f355e205e44fc`)
- Controlled Polygon authority evidence intake specification: `PHASE19_PRODUCTION_AUTHORITY_EVIDENCE_INTAKE.md`
- Controlled Polygon authority evidence validator: `scripts/validate_production_authority_evidence.py`
- Controlled Polygon authority validator tests: `tests/phase19/test_production_authority_evidence_validator.py`
- Production readiness decision: **NOT ACHIEVED**
- Controlled production signer identity: **BLOCKED**. No fresh externally held production-signer challenge signature and provenance record is present; the signer runbook explicitly states mechanism-level CI is insufficient for this gate.
- Controlled production Polygon provider authority: **BLOCKED**. The repository-side authority observation path and offline evidence validator are now prepared, but no controlled production observation evidence from explicitly approved endpoints is present.
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
Deterministic economics, immutable authorization/envelope binding, quote and simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, private-only submission, recovery, receipt reconciliation, executor controls, and authority quorum/provenance/freshness controls are implemented. #420, #423, #427, #430, #432, #435, #436, and #437 provide the latest certified gates.

The production chain observer is read-only and requires a unique quorum-backed decision. fileciteturn1534file0L2-L2

The execution-observation path requires an exact, previously persisted and fresh quorum record before lifecycle persistence. fileciteturn1545file0L2-L2

Settlement reconciliation has a dedicated quorum boundary, and the lower-level settlement primitive is explicitly treated as an already-admitted path. fileciteturn1548file0L2-L2

Recovery mutation has the same quorum provenance boundary for DROP, REPLACED, and REORGED evidence. fileciteturn1549file0L2-L2

The production signer verifier can generate a fresh 32-byte challenge and independently verify an externally supplied 65-byte signature without receiving private-key material. fileciteturn1577file0L2-L2

The production authority module remains environment-driven and read-only, requiring explicit operator-supplied provider configuration and validating HTTPS endpoints, executor identity, and expected signer before authority observation. fileciteturn1564file0L2-L2

The production private-relay assembly requires explicit HTTPS configuration and `private=true` and has no public fallback. fileciteturn1573file0L2-L2

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Controlled shadow/staging evidence using the identical immutable artifact chain.
5. Controlled realized live settlement/PnL evidence satisfying strict `net > $0.20` after all applicable costs.
6. Independent re-audit after all production gates are evidenced.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
The latest software-side addition is the controlled Polygon authority evidence intake contract, validator, and adversarial validator tests. These are repository-side readiness infrastructure only; they do not constitute production authority proof.

GitHub Actions workflow run `442` is currently **IN PROGRESS** against the authority-validator test commit `7f5a839bd5968961f23dff27b9dfa8da41539993`. Its completed steps so far are dependency installation, Foundry installation, Solidity compilation, EVM integration, and Polygon fork protocol smoke. The Polygon fork execution probe is still running, so no GREEN claim is permitted yet.

The latest completed certification remains workflow run `439` / run ID `35018490583`, GREEN on software commit `ebf794537c531a1241426a2bca9f355e205e44fc`.

The signer gate remains BLOCKED pending real external evidence. The Polygon authority gate remains BLOCKED pending controlled observations from explicitly approved production endpoints.

## NEXT ATOMIC ACTION
Inspect workflow run `442` to completion. If it fails, freeze and repair only the failed boundary. If it succeeds, certify the new authority-evidence validator, then proceed to the controlled production Polygon authority observation procedure without treating public/fork endpoints as production authority. Keep signer, relay, shadow, realized-PnL, and live-capital gates locked.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
