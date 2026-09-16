# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize only on substantive state transitions. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified engineering commit: `213c781368af684ce9af58daeacdf2baade6c453`
- Latest verified Phase-19 CI certification: workflow run `496` / run ID `35096413145` **GREEN** on `213c781368af684ce9af58daeacdf2baade6c453`; dependency install, Foundry install, Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, full Phase-19 unittest suite, and post-verification steps all passed
- External evidence session artifact remains frozen at `e117b6550686cf5e0ff787d9bd7d85e83996db07` until a deliberate new evidence session is started; newer toolchain commits do not retroactively alter that evidence identity
- External gate launch packet currently present at `PHASE19_EXTERNAL_GATE_LAUNCH_PACKET.md`; its frozen evidence identity is `e117b655...`
- One-shot external gate worksheet is maintained as a repository-side procedure artifact; its frozen evidence identity is `e117b655...`
- Controlled signer evidence validator: `scripts/validate_signer_evidence.py`
- Controlled Polygon authority evidence validator: `scripts/validate_production_authority_evidence.py`
- Controlled private-relay evidence validator: `scripts/validate_private_relay_evidence.py`
- Consolidated external evidence session coordinator: `scripts/validate_consolidated_evidence_session.py`
- Batched Phase-19 gate console: `scripts/phase19_gate_console.py`
- Shadow/staging evidence validator: `scripts/validate_shadow_staging_evidence.py`
- Realized-PnL evidence validator: `scripts/validate_realized_pnl_evidence.py`
- Realized-PnL provenance rule: arithmetic validation does not constitute independent proof of actual settlement
- Signer evidence packager: `scripts/package_signer_evidence.py`; canonical challenge/evidence-hash binding is CI-verified by workflow run `#496`
- Historical deployment-record forensic finding: older commit `8460c589ef6b82b1da08d73624f29d0cd63d2549` contains historical Polygon deployment assertions; these remain forensic only and are not accepted as current production-authority evidence
- Certification PR `#1`: **OPEN / MERGE CONFLICTS**. Current integration head is allowed to move with documentation-only sync commits; merge is not required for external evidence capture and is not treated as a production gate.
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
The latest verified engineering toolchain is **`213c781368af684ce9af58daeacdf2baade6c453` with workflow run `496` GREEN**. The external evidence identity remains deliberately frozen at **`e117b655...`** until a new evidence session is created. Signer evidence packaging and canonical hash binding are CI-verified. The current certification PR remains an integration item with merge conflicts, not a production authorization gate.

The remaining gates are external and evidence-backed: genuine controlled signer proof, Polygon provider authority proof, approved private relay observation, identical-artifact shadow/staging evidence, realized net-PnL evidence, and final independent re-audit. No external production evidence has been accepted yet.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**