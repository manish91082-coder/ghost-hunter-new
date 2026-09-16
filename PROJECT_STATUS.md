# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize only on substantive state transitions. Evidence first, fail closed, no fabricated passes.

## CURRENT MISSION
The project goal is not Phase-19. The goal is a working, evidence-backed Polygon flash-loan arbitrage MVP that can progress from real market opportunity discovery through exact route economics, simulation, controlled execution, on-chain settlement, and proof that realized net profit is strictly greater than $0.20 after all applicable costs.

## CURRENT MVP ORDER
1. Real opportunity discovery.
2. Exact live quotes at one pinned block.
3. Executable A→B→A route construction.
4. Complete worst-case economics and strict `net > $0.20` gate.
5. Deterministic execution assembly and EVM preflight.
6. Governor/safety controls.
7. External signer/provider/private-relay/shadow verification.
8. Controlled execution.
9. Settlement reconciliation.
10. Realized PnL proof `> $0.20`.
11. Independent final audit and release freeze.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified engineering commit: `1dbadae395426f9c53f94ad052a4565c499b6575`
- Latest verified Phase-19 CI certification: workflow run `521` / run ID `35133216772` **GREEN** on `1dbadae395426f9c53f94ad052a4565c499b6575`; compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full Python Phase-19 suite all passed.
- New MVP integration milestone: `phantomx/mvp_pipeline.py` connects exact route acquisition → strict economic proof → deterministic execution assembly as one pre-execution pipeline. It does not sign, submit, broadcast, or touch live capital.
- New regression coverage: `tests/phase19/test_mvp_pipeline.py` covers successful assembly, strict profit-floor rejection, invalid EIP-1559 fee bounds, and read-only RPC discipline.
- Prior failed CI run `520` was isolated to the new fee-bound regression: the pipeline allowed an invalid `max_priority_fee_per_gas > max_fee_per_gas` input to reach assembly instead of rejecting it early. This was corrected in `1dbadae...`; run `521` then passed.
- Current status synchronization is documentation-only and does not constitute engineering certification.
- Frozen external evidence artifact remains `e117b6550686cf5e0ff787d9bd7d85e83996db07`; engineering commits after that artifact do not retroactively alter its identity.
- Consolidated external-evidence validator hard-binds the session manifest artifact identity to the frozen external artifact.
- Operator preflight requires the frozen artifact in local history and current HEAD to descend from it.
- Required external-evidence validators remain present for signer, Polygon authority, private relay, shadow/staging, and realized PnL.
- Certification PR `#1`: **OPEN / MERGE CONFLICTS**; merge is not required for external evidence capture.
- External evidence handoff issue `#2`: **OPEN / BLOCKED**; genuine current production evidence has not been accepted.
- Production readiness: **NOT ACHIEVED**
- Controlled production signer identity: **BLOCKED**
- Controlled production Polygon provider authority: **BLOCKED**
- Controlled production private relay: **BLOCKED**
- Controlled shadow/staging: **BLOCKED**
- Realized live PnL: **BLOCKED**
- Live mainnet execution: **BLOCKED**
- Live capital: **LOCKED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## OPERATING MODE
Each `next` is a batch execution cycle: scan the complete mission state, identify the highest-value unresolved bottleneck, execute all independent repository-safe work that materially advances the mission, verify it, integrate it, and only then advance. Phase-19 is treated as an external verification gate, not as the project goal.

## SAFETY
No private key, seed phrase, keystore password, relay credential, authentication secret, raw signed transaction, public fallback, live broadcast, or live-capital operation is permitted in the certification workspace.

## P0 BLOCKERS
1. Real opportunity must be proven genuine and currently executable.
2. Controlled production signer identity proof.
3. Controlled production Polygon provider authority proof.
4. Controlled production private relay proof.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Controlled realized settlement/PnL evidence with strict `net > $0.20` after all applicable costs.
7. Independent final re-audit.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**