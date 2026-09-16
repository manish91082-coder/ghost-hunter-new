# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize only on substantive state transitions. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified engineering commit: `213c781368af684ce9af58daeacdf2baade6c453`
- Latest verified Phase-19 CI certification: workflow run `496` / run ID `35096413145` **GREEN** on `213c781368af684ce9af58daeacdf2baade6c453`; dependency install, Foundry install, Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, full Phase-19 unittest suite, and post-verification steps all passed
- Verified acceleration sequence: `fa0248c7a427949809baf7fd59ae199eaa54495e` (batched gate console) → `eb11a60783bd5da60d5e4ce7cfcc3b06ac5379d9` (shadow fixture alignment) → `a2ed8e2989b37a750f25bf564a4322732129058e` (fail-closed gate-console tests) → `5781b473f045faeeb515d3e0e419b449afbc9e00` (cross-lane binding coordinator) → `fc0df125ee6d0ea694b976ff7d86622b9e45eb15` (binding test correction) → `1d7792480798abb7844b3cc09c08e0e41fafde86` / `1c6e6fb1...` / `70aa358d...` (realized-PnL validation/provenance sequence) → `84f0c22a3350149a2c02e1aeba04da6fac13cb26` (relay-binding fixture alignment) → `06ebded9e09677e9235a4d0e18e347d9375368e6` / `aa3eb69102c9aa6de337ae4dd027a90f90291aac` / `e117b6550686cf5e0ff787d9bd7d85e83996db07` (private-relay and cross-lane provenance hardening) → `d2121e2fc0f866182ef42a9373ff6aba6b189a57` (one-shot external session launcher) → `c2db3e6a6ac861b207bea9bf1e6252d32ae291e0` (operator preflight) → `46ab733fa4eca81c24eeaf087c9c44a71eb987e6` (verified toolchain-head preflight fix) → `e9d924...` / `827814...` / `e754a0...` / `ff5a5503...` / `213c781368af684ce9af58daeacdf2baade6c453` (signer evidence packaging, regression repair, canonical hash-binding hardening; final commit CI-verified by #496)
- Documentation-only synchronization commits after the verified engineering baseline do not supersede that verified engineering commit.
- Previous verified Phase-19 CI certification: workflow run `490` / run ID `35093381297` **GREEN** on `46ab733fa4eca81c24eeaf087c9c44a71eb987e6`
- External evidence session artifact remains frozen at `e117b6550686cf5e0ff787d9bd7d85e83996db07` until a deliberate new evidence session is started; newer toolchain commits do not retroactively alter that evidence identity
- External gate launch packet currently present at `PHASE19_EXTERNAL_GATE_LAUNCH_PACKET.md`; its frozen evidence identity is `e117b655...`
- One-shot external gate worksheet is maintained as a repository-side procedure artifact; its frozen evidence identity is `e117b655...`
- Latest repository-side procedure/launch worksheet refresh lineage includes `eddcc2379769d3151af4091832566db6ae1ea3f6`, `36718fca0eae97b7ad03b648766cfaad3407f545`, and `095e9295244d350374fc40dadc8d80f2d1287831`
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
- Consolidated coordinator binds accepted signer, Polygon authority, private relay, shadow/staging, and realized-PnL evidence to manifest-level signer, executor, artifact, private-relay, operator, and witness identities; absolute evidence paths are rejected and relative paths resolve from the external manifest workspace
- Cross-lane provenance binding: canonical evidence hashes may be joined authority → shadow/staging → realized-PnL; mismatches fail closed while legacy opaque fixture labels remain accepted for compatibility
- Shadow/staging evidence validator: `scripts/validate_shadow_staging_evidence.py`
- Realized-PnL evidence validator: `scripts/validate_realized_pnl_evidence.py`
- Realized-PnL provenance rule: arithmetic validation does not constitute independent proof of actual settlement
- Signer evidence packager: `scripts/package_signer_evidence.py`; canonical challenge/evidence-hash binding is CI-verified by workflow run `#496`
- Signer packager adversarial/regression tests: CI-verified by workflow run `#496`
- Shadow/staging validator tests use a frozen verified-artifact fixture; latest CI-verified engineering code is `213c7813...`
- Historical deployment-record forensic finding: older commit `8460c589ef6b82b1da08d73624f29d0cd63d2549` contains historical Polygon deployment assertions; these remain forensic only and are not accepted as current production-authority evidence
- Certification PR `#1`: **OPEN / MERGE CONFLICTS**. Current head is `213c7813...`; merge is not required for external evidence capture and is not being treated as a production gate.
- External evidence handoff issue `#2`: **OPEN / BLOCKED**. No current production evidence package has been accepted.
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
The latest verified engineering toolchain is **`213c781368af684ce9af58daeacdf2baade6c453` with workflow run `496` GREEN**. The external evidence identity remains deliberately frozen at **`e117b655...`** until a new evidence session is created. Signer evidence packaging and canonical hash binding are now CI-verified. The current certification PR remains an integration item with merge conflicts, not a production authorization gate.

The remaining gates are external and evidence-backed: genuine controlled signer proof, Polygon provider authority proof, approved private relay observation, identical-artifact shadow/staging evidence, realized net-PnL evidence, and final independent re-audit. No external production evidence has been accepted yet.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**