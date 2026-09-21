# PHANTOMX PROJECT MEMORY
# Durable cross-chat project memory for PHANTOMX / Flash Loan Ghost Hunter

## Canonical identity
- Repository: `manish91082-coder/ghost-hunter-new`
- Canonical branch: `phase-19-e2e-harness`
- Base branch: `master`
- Chain: Polygon PoS, chain ID 137
- Flash liquidity: Aave V3
- Canonical MVP route family: direct A→B→A, QuickSwap V2 ↔ Uniswap V3
- Production signing/broadcast/capital: BLOCKED / BLOCKED / LOCKED

## Immutable economic mission
Realized net profit must be strictly greater than $0.20 after all applicable transaction-attributable costs. Gross-positive, post-flash-positive, quote-positive, unit-test success, fork success, or historical observations are not realized-profit proof.

## Durable operating rule
GitHub is the source of truth. Chat memory is supporting context only.
Before every repository write: verify repository, branch, current HEAD, manifest, PROJECT_STATUS, relevant Actions, commits, and reconcile contradictions.
Every substantive cycle must synchronize:
1. this PROJECT_MEMORY.md;
2. PHANTOMX_PROJECT_RESUME_MANIFEST.md;
3. PROJECT_STATUS.md;
4. relevant evidence/strategy/security documents.
PROJECT_DETAILS.md is updated whenever architecture/scope/operating-contract facts materially change. This is deliberate, not a blind per-message rewrite.

## Current verified state • 2026-09-21
- Latest observed canonical branch HEAD before this memory commit will be recorded by the next status/manifest synchronization.
- Semantic-revert discovery repair:
  - `014e14ed25859a80d0f057c3e6de76adac1d4cb3`
  - `864f45b9418cf019bd4f6ab1acda4bb2bd565f21`
- Exact-head Phase-19 verification:
  - run #953 / `35566476152` GREEN on `a9cb6aca...`
  - run #954 / `35566623730` GREEN on `3643648d...`
- Fresh First-Hunt #68 / `35566476146` completed successfully on exact hunt HEAD `a9cb6aca...`.
- First-Hunt #68 coverage: 36/36 tiles COMPLETE; 36/36 shards accounted; 1,246 exact observations; 0 gross-positive; 0 post-flash-positive.
- First-Hunt #68 pinned market block: 94,176,798 on Polygon chain 137.
- Best gross observation: `-$0.115879` USDC.
- Best post-flash observation: `-$0.165879` USDC.
- Aave flash premium observed in the hunt: 5 bps.
- Hunt economic certification: NOT_PERFORMED. Therefore the hunt is complete discovery/coverage evidence, not an EconomicProof or profitability certificate.
- Four tiles reached COMPLETE_NO_COMMON_ROUTE; they are valid terminal coverage outcomes, not missing coverage.
- Exact gas, live native valuation, relay/MEV costs, final requote/state lock, EVM preflight, external authority/signer/relay/shadow gates, execution, receipt reconciliation and realized PnL remain separate gates.
- Historical Polygon Universe campaign remains open; historical exhaustion is not claimed.
- Current canonical repository inventory: 318 tracked files after the surgical cleanup lineage.
- Surgical deletion evidence remains limited to proven temporary artifacts; master remains untouched.

## Safety locks
LIVE SIGNING = BLOCKED
PUBLIC BROADCAST = BLOCKED
LIVE CAPITAL = LOCKED

## Next deterministic gate
1. Record First-Hunt #68 evidence as a dedicated cycle artifact.
2. Synchronize PROJECT_DETAILS, manifest, PROJECT_STATUS and this memory against the actual current HEAD.
3. Reconcile whether complete S0 coverage is sufficient for the next economic/execution-path integration step.
4. Do not promote any observation to profitability without complete EconomicProof and subsequent gates.[object Object]

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S1 CURRENT-HEAD REFRESH
- S0 First-Hunt #68 is terminal and complete for its declared 36-cell domain: 36/36 coverage, 1,246 observations, 0 gross-positive, 0 post-flash-positive at Polygon block 94,176,798; no profitability certificate.
- To refresh the next existing discovery lane on the repaired lineage, the S1 workflow received a comment-only control-plane trigger. No S1 scanner/route/economic implementation was changed.
- Current S1 trigger HEAD: `af93d56fd7c1cf7b6cb2dd494abb8cffc542752f`.
- S1 QuickSwap V3 ↔ Uniswap V3 live read run #40 / ID `35574659400` is active on that exact HEAD.
- Exact-head Phase-19 run #960 / ID `35574659415` is active on the same HEAD; neither is yet terminal.
- No S1 market conclusion is admissible until the exact-head CI result and S1 evidence artifact are both available.
- Safety remains unchanged: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S1 COVERAGE REPAIR
- S1 live-read run #40 / `35574659400` on scanner HEAD `af93d56...` completed successfully at workflow level, but its artifact exposed **28/36 successful tiles and 8 UNAVAILABLE_OR_FAILED tiles**. Therefore it is explicitly classified as incomplete evidence, not a market-negative certificate.
- The S1 scanner previously returned exit code 0 whenever the RPC pool produced any result, even when tile-level evidence was unresolved. This violated fail-closed coverage discipline.
- Surgical repair commits:
  - `3612cade...`: import/discovery boundary preparation.
  - `a55827ff...`: explicit S1 tile coverage classification and retry-boundary helpers.
  - `faf746cb...`: preserve per-tile terminal/incomplete evidence in the S1 artifact.
  - `ff922485...`: make S1 return non-zero when any declared tile remains incomplete.
  - `39ea509...`: regression tests for incomplete, terminal-no-route and complete-common-route classification.
  - `2269aaab...`: fix unittest import-path compatibility.
- Exact-head Phase-19 run #969 / ID `35576798169` is GREEN on `2269aaab...`, including compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe and the full unittest suite.
- Corrected S1 run #45 / ID `35576798186` is pending because an older S1 run #41 on an earlier lineage still occupies the shared S1 concurrency group. Run #41 is not admissible current-head evidence.
- No new profitability claim is made. S1 #40 had 1,120 route observations, 0 gross-positive observations, and dynamic Aave ceiling 596,890 USDC, but its 8 unresolved tiles prevent a complete S1 market certificate.
- Production remains blocked: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S1 COVERAGE REPAIR EVIDENCE RECORDED
- Dedicated audit record: `PHANTOMX_S1_COVERAGE_REPAIR_EVIDENCE_2026-09-21.md`, documenting S1 #40's 28/36 successful versus 8 unresolved tiles, the root cause, surgical repair and verification.
- The corrected S1 scanner is fail-closed on unresolved tile coverage.
- Phase-19 #969 / `35576798169` is GREEN on repair HEAD `2269aaab...`.
- Corrected S1 run #45 / `35576798186` targets `2269aaab...` and remains queued behind an older in-flight S1 run #41; #41 is not admissible current evidence.
- S0 #68 remains complete only for its declared bounded 36-cell matrix, with no gross-positive or post-flash-positive observation.
- Safety remains unchanged: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.
