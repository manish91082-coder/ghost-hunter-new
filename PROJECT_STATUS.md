# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize only on substantive state transitions. Evidence first, fail closed, no fabricated passes.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Latest verified engineering commit: `2c42974945a925868b9a6d27598f30241e9c481c`
- Latest verified Phase-19 CI certification: workflow run `517` / run ID `35128971266` **GREEN** on `2c42974945a925868b9a6d27598f30241e9c481c`; complete Phase-19 workflow passed including Solidity compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full Phase-19 unittest suite
- Frozen external evidence artifact remains `e117b6550686cf5e0ff787d9bd7d85e83996db07`; engineering commits after that artifact do not retroactively alter its identity
- Consolidated external-evidence validator now enforces that the session manifest `verified_artifact_commit` equals the frozen external evidence artifact
- Operator preflight now requires the frozen artifact to be present in local git history and requires current HEAD to descend from that artifact, removing the brittle historical head allow-list while retaining fail-closed ancestry validation
- Required external-evidence validators remain present for signer, Polygon authority, private relay, shadow/staging, and realized PnL
- Certification PR `#1`: **OPEN / MERGE CONFLICTS**; merge is not required for external evidence capture
- External evidence handoff issue `#2`: **OPEN / BLOCKED**; no current production evidence package has been accepted
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
Each `next` is a batch execution cycle: complete state scan first, then execute all independent repository-safe work that materially advances the mission, verify it, integrate it, and only then synchronize status. Missing or contradictory external evidence remains BLOCKED.

## SAFETY
No private key, seed phrase, keystore password, relay credential, authentication secret, raw signed transaction, public fallback, live broadcast, or live-capital operation is permitted in the certification workspace.

## P0 BLOCKERS
1. Controlled production signer identity proof.
2. Controlled production Polygon provider authority proof.
3. Controlled production private relay proof.
4. Controlled shadow/staging evidence using the identical immutable artifact chain.
5. Controlled realized settlement/PnL evidence with strict `net > $0.20` after all applicable costs.
6. Independent final re-audit.

**LIVE SIGNING = BLOCKED**
**PUBLIC BROADCAST = BLOCKED**
**LIVE CAPITAL = LOCKED**
