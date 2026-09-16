# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize only on substantive state transitions. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified engineering commit: `213c781368af684ce9af58daeacdf2baade6c453`
- Latest verified Phase-19 CI certification: workflow run `496` / run ID `35096413145` **GREEN** on `213c781368af684ce9af58daeacdf2baade6c453`; dependency install, Foundry install, Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, full Phase-19 unittest suite, and post-verification steps all passed
- External evidence session artifact remains frozen at `e117b6550686cf5e0ff787d9bd7d85e83996db07` until a deliberate new evidence session is started; newer toolchain commits do not retroactively alter that evidence identity
- Controlled signer evidence validator: `scripts/validate_signer_evidence.py`
- Controlled Polygon authority evidence validator: `scripts/validate_production_authority_evidence.py`
- Controlled private-relay evidence validator: `scripts/validate_private_relay_evidence.py`
- Consolidated external evidence session coordinator: `scripts/validate_consolidated_evidence_session.py`
- Batched Phase-19 gate console: `scripts/phase19_gate_console.py`
- Shadow/staging evidence validator: `scripts/validate_shadow_staging_evidence.py`
- Realized-PnL evidence validator: `scripts/validate_realized_pnl_evidence.py`
- Signer evidence packager: `scripts/package_signer_evidence.py`; canonical challenge/evidence-hash binding is CI-verified by workflow run `#496`
- Certification PR `#1`: **OPEN / MERGE CONFLICTS**; merge is not required for external evidence capture and is not treated as a production gate
- External evidence handoff issue `#2`: **OPEN / BLOCKED**; no current production evidence package has been accepted
- Production readiness decision: **NOT ACHIEVED**
- Controlled production signer identity: **BLOCKED**
- Controlled production Polygon provider authority: **BLOCKED**
- Controlled production private relay: **BLOCKED**
- Controlled shadow/staging: **BLOCKED**
- Realized live PnL: **BLOCKED**
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## ACCELERATED OPERATING MODE
Each `next` is now a batch execution cycle: scan the complete state, execute all independent repository-safe work that can advance, run/observe verification, integrate results, and only then synchronize status. No-op status commits are avoided.

Repository-safe work and evidence preparation run in parallel. External production facts remain independently evidence-gated.

Current lanes: A Polygon production authority, B production signer identity, C private relay, D identical-artifact shadow/staging, E realized economics/PnL.

## SAFETY
Evidence first. Contradictory or missing evidence is UNKNOWN/BLOCKED. Private execution has no public fallback. No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification. Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## VERIFIED SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof.
3. Controlled production private relay proof.
4. Controlled shadow/staging evidence using the identical immutable artifact chain.
5. Controlled realized live settlement/PnL evidence satisfying strict `net > $0.20` after all applicable costs.
6. Independent re-audit after all production gates are evidenced.
7. Live mainnet capital deployment remains forbidden.

## CHECKPOINT
The latest verified engineering toolchain is **`213c781368af684ce9af58daeacdf2baade6c453` with workflow run `496` GREEN**. The external evidence identity remains deliberately frozen at **`e117b655...`** until a new evidence session is created. The remaining gates are external and evidence-backed. No external production evidence has been accepted yet.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**