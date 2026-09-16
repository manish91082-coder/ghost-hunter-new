# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize only on substantive state transitions. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified engineering commit: `fc0df125ee6d0ea694b976ff7d86622b9e45eb15`
- Latest verified Phase-19 CI certification: workflow run `467` / run ID `35082865445` **GREEN** on `fc0df125ee6d0ea694b976ff7d86622b9e45eb15`; dependency install, Foundry install, Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, full Phase-19 unittest suite, and post-verification steps all passed
- Verified acceleration sequence: `fa0248c7a427949809baf7fd59ae199eaa54495e` (batched gate console) → `eb11a60783bd5da60d5e4ce7cfcc3b06ac5379d9` (shadow fixture alignment) → `a2ed8e2989b37a750f25bf564a4322732129058e` (fail-closed gate-console tests) → `5781b473f045faeeb515d3e0e419b449afbc9e00` (cross-lane binding coordinator) → `fc0df125ee6d0ea694b976ff7d86622b9e45eb15` (binding test correction)
- Status synchronization commits are documentation-only and do not supersede the latest verified engineering commit unless a later code change is independently CI-verified.
- Previous verified Phase-19 CI certification: workflow run `464` / run ID `35082135017` **GREEN** on `a2ed8e2989b37a750f25bf564a4322732129058e`
- Latest repository-side procedure/launch worksheet commit: `095e9295244d350374fc40dadc8d80f2d1287831`
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
- Controlled signer evidence validator: `scripts/validate_signer_evidence.py`
- Controlled Polygon authority evidence intake specification: `PHASE19_PRODUCTION_AUTHORITY_EVIDENCE_INTAKE.md`
- Controlled Polygon authority observation runbook: `PHASE19_PRODUCTION_AUTHORITY_OBSERVATION_RUNBOOK.md`
- Controlled Polygon authority evidence validator: `scripts/validate_production_authority_evidence.py`
- Controlled private-relay evidence intake specification: `PHASE19_PRIVATE_RELAY_EVIDENCE_INTAKE.md`
- Controlled private-relay evidence validator: `scripts/validate_private_relay_evidence.py`
- Consolidated external evidence session protocol: `PHASE19_CONSOLIDATED_EXTERNAL_EVIDENCE_SESSION.md`
- Consolidated external evidence session coordinator: `scripts/validate_consolidated_evidence_session.py`
- Batched Phase-19 gate console: `scripts/phase19_gate_console.py`
- Consolidated coordinator now binds accepted signer, Polygon authority, and shadow/staging evidence to manifest-level signer, executor, artifact, operator, and witness identities; absolute evidence paths are rejected and relative paths resolve from the external manifest workspace
- External gate launch packet: `PHASE19_EXTERNAL_GATE_LAUNCH_PACKET.md` (frozen to prior verified artifact `eea845af...`; must be reissued before any external evidence is accepted against a newer artifact)
- One-shot external gate session worksheet: `PHASE19_OPERATOR_ONE_SHOT_SESSION.md` (frozen to prior verified artifact `eea845af...`; must be reissued before any external evidence is accepted against a newer artifact)
- Shadow/staging evidence validator: `scripts/validate_shadow_staging_evidence.py`
- Shadow/staging validator tests use a frozen verified-artifact fixture; latest CI-verified engineering code is `fc0df125...`
- Historical deployment-record forensic finding: older commit `8460c589ef6b82b1da08d73624f29d0cd63d2549` contains historical Polygon deployment assertions; these remain forensic only and are not accepted as current production-authority evidence
- Production readiness decision: **NOT ACHIEVED**
- Controlled production signer identity: **BLOCKED**. No fresh externally held production-signer challenge signature and provenance record is present.
- Controlled production Polygon provider authority: **BLOCKED**. No controlled production observation evidence from explicitly approved endpoints is present.
- Controlled production private relay: **BLOCKED**. No approved production relay observation evidence is present.
- Controlled shadow/staging: **BLOCKED**. No independently evidenced staging execution artifact is present.
- Realized live PnL: **BLOCKED**. No controlled live-mainnet realized settlement evidence exists and live capital remains locked.
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## ACCELERATED OPERATING MODE
Each `next` is now a batch execution cycle: scan the complete state, execute all independent repository-safe work that can advance, run/observe verification, integrate results, and only then synchronize status. No-op status commits are avoided.

Repository-safe work and evidence preparation run in parallel. External production facts remain independently evidence-gated.

Current lanes:
- A: Polygon production authority evidence
- B: production signer identity evidence
- C: private-relay evidence
- D: identical-artifact shadow/staging evidence
- E: realized economics/PnL evidence

The batched gate console creates one deterministic session manifest from the standard segregated evidence workspace so the operator can prepare all lanes in one pass instead of manually assembling repeated single-lane commands. Presence of an evidence file remains **BLOCKED** until its dedicated validator accepts the evidence.

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Controlled shadow/staging evidence using the identical immutable artifact chain.
5. Controlled realized live settlement/PnL evidence satisfying strict `net > $0.20` after all applicable costs.
6. Independent re-audit after all production gates are evidenced.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
The current **verified engineering baseline is `fc0df125...` with workflow run `467` GREEN**. The consolidated Phase-19 coordinator now has session-level identity binding and supports evidence workspaces outside the repository while retaining path traversal protection. This is an integration-hardening milestone only; it does not authorize production execution.

External gate launch documents remain stale because they are frozen to `eea845af...`. They must be regenerated for the current verified artifact before any genuine external evidence can be accepted.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**