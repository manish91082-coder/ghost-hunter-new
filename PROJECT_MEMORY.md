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

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 CURRENT-HEAD REFRESH IN PROGRESS
- S1 corrected run #45 / `35576798186` is **GREEN** with its repaired scanner lineage; its current evidence must be treated as the latest bounded S1 read. Earlier S1 #40 remains historical/incomplete evidence and was superseded by the fail-closed repair.
- S3 Ramses V3 ↔ Uniswap V3 refresh trigger commit: `34023ae5f88da0dec7ac3e837b89a5fd8ae39b1d`.
- Exact-head Phase-19 run #977 / ID `35578078308` is **GREEN** on the S3 trigger HEAD. Compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and full unittest suite all passed.
- S3 live-read run #17 / ID `35578078265` is still active in its read-only scanner step. No S3 market result is admissible until its evidence artifact is published and coverage/economic fields are inspected.
- S0 #68 remains complete only for its declared 36-cell bounded domain; S1 #45 is the repaired current-head S1 evidence; S3 is now the active next strategy lane.
- Production remains fail-closed: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 COVERAGE REPAIR IMPLEMENTED

- Canonical HEAD is `3ea4d347f1d400232342f5f44c93a5a9948e93c8`.
- S3 run #17 / `35578078265` exposed a coverage-model defect: 168/168 declared tiles were stored as `UNAVAILABLE_OR_FAILED`; 164 were deterministic Ramses pool absence and 4 were RPC semantic reverts. The artifact therefore could not support a complete S3 conclusion despite workflow success.
- Repair `0213dea08fffbc30256ded62dd5b91c28b605936` makes S3 fail closed on unresolved coverage and distinguishes terminal no-route cells from incomplete cells.
- Regression commit `3ea4d347f1d400232342f5f44c93a5a9948e93c8` is verified by Phase-19 #982 / `35580051618` GREEN with 899 tests.
- S3 run #18 / `35579964402` is the current repair verification run and remains in progress. Until its terminal artifact is parsed, S3 market status is UNKNOWN/BLOCKED, not negative and not positive.
- The safety contract is unchanged: no signing, public broadcast, or live capital.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 RUN #19 + RPC AMBIGUOUS-REVERT REPAIR

- S3 #19 preserved artifact evidence and confirmed 164 terminal no-route cells plus 4 unresolved `Unexpected error` cells, with no observations.
- RPC repair `f499920edb177680c04d0bd7ce3749af131394dd` makes only the uninformative `execution reverted: Unexpected error` recoverable across the bounded free-provider fleet; reasoned execution reverts remain non-recoverable.
- Regression commit `ba4d347c9d5fe9471aab06cdbe8797ac358f7146` is verified by Phase-19 #986 / `35581593367` GREEN with 901 tests.
- S3 current-head refresh after this repair is the next proof boundary. Until its artifact is inspected, S3 remains UNKNOWN/BLOCKED.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • CANONICAL RPC REPAIR REAPPLIED

- Live-tree verification exposed a content-lineage mismatch in `d98befea...`: its tree retained the old RPC revert policy.
- The RPC ambiguity repair is being reapplied directly to the current canonical tree and will be re-verified by Phase-19 and a fresh S3 current-head run.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 #23 COMPLETE

- S3 #23 `35595059504` is complete for its declared 168-tile matrix on `4028cdd375b3455b2d4b3972506b669058d9e6f6`.
- Coverage: 168/168 complete; 164 terminal no-route; 4 common-route tiles; 160 observations; 0 gross-positive; best gross `-$0.009175`; best post-flash `-$0.059175`.
- Pair universe is `COMPLETE_RECENT_WINDOW` with 7 active seeded pairs. Dynamic Aave ceiling is 597079.810291 USDC at 5 bps premium.
- No economic certificate or profit claim exists. S3 is bounded complete-discovery evidence only.
- Phase-19 #991 is GREEN with 902 tests. Next lane is S5 after current-workflow inspection.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3/S9/S10 BOUNDED DISCOVERY VERIFIED

- Canonical branch: `phase-19-e2e-harness`; current HEAD at this sync: `4f34922748c170bb506948239c5db0ad369aee90`.
- Phase-19 run #1012 / `35606425572` is GREEN on `4f34922748c170bb506948239c5db0ad369aee90`: compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and **918** unittest tests passed.
- S3 run #26 / `35603762763` on `414ccd02db181f752525845cdca3bf5e61e46daa` is applicable to current strategy code because the compare path from that commit to the current HEAD changes only S9/S10 scanners/workflows and the dynamic-pair regression-test lineage, not S3 scanner/adapter/route code. S3 artifact `10641495828`, ZIP digest `sha256:e08788366ae9c4fc89634372019d815d77822bb98291740041e5c74a9202fca0`: **168/168 tiles complete**, 164 terminal no-route, 4 complete route tiles, 160 observations, 0 gross-positive; best gross `-$0.009316` USDC; economic certification `NOT_PERFORMED`, profit claim `NONE`.
- S9 run #19 / `35606425568` on `4f349227...`: artifact `10643105338`, ZIP digest `sha256:721e76d48a431b08fe4c8a7f82c4c46c00c21250528f6fb2f231c7834b115263`; extracted JSON SHA-256 `8388652378682bba64c554aebada73f2ceeb9db8aeda581d8d04ec727f81cfa7`. Coverage is **42/42 complete**: 41 `COMPLETE_NO_COMMON_ROUTE`, 1 `COMPLETE`; 40 exact observations; 0 gross-positive; best gross `-$0.164940` USDC; best post-flash `-$0.214940` USDC; Aave liquidity `628504.358728` USDC; dynamic ceiling `597079.140791` USDC; flash premium 5 bps; pair universe `COMPLETE_RECENT_WINDOW`, 7 active pairs.
- S10 run #19 / `35606425570` on `4f349227...`: artifact `10643145202`, ZIP digest `sha256:7f1dfb10632387a916efe7a6fa04efe7cdb8f84d31ad5de56fc53e250593970e`; extracted JSON SHA-256 `8cb018257c00462929d64726f3510be80e3cf806943b1aff6ee74da139b215b0`. Coverage is **42/42 complete**: 41 `COMPLETE_NO_COMMON_ROUTE`, 1 `COMPLETE`; 40 exact observations; 0 gross-positive; best gross `-$0.002202` USDC; best post-flash `-$0.052202` USDC; Aave liquidity `628504.358728` USDC; dynamic ceiling `597079.140791` USDC; flash premium 5 bps; pair universe `COMPLETE_RECENT_WINDOW`, 7 active pairs.
- The repaired S9/S10 scanner contract is now fail-closed: unresolved/retryable execution evidence prevents certification, deterministic missing-pool cases become terminal no-route, aggregate coverage must be complete, and artifacts are preserved on scanner failure.
- S5 run #22 / `35604456371` remains an older-head live run on `73edc2c40e74e347e3925c2673a3f1123d8821f4`; it is not current-HEAD evidence. A fresh S5 current-head run is still required after that run terminalizes.
- No strategy evidence above is an EconomicProof or profitability certificate. No signing, submission, public broadcast, live capital, or realized-PnL claim is authorized.
- Safety: **LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.**
- Durable evidence record: `PHANTOMX_S9_S10_COVERAGE_REPAIR_EVIDENCE_2026-09-21.md`.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • CONTROL-PLANE ISOLATION

- Current canonical HEAD before this memory synchronization: `5f7c486d81d36ad2934d7976c70340ed375dd3db`.
- A dedicated control-plane repair removed push triggers from the market/inventory workflow set so normal code changes do not fan out multiple live-read hunts.
- S5 is the deliberate exception: it has a narrow push trigger on `.github/PHANTOMX_S5_KICK` only, preserving an explicit controlled refresh mechanism without coupling S5 to generic implementation changes.
- Regression policy is encoded in `tests/phase19/test_market_workflow_trigger_policy.py`; the exact-head Phase-19 run #1019 / `35621384834` completed GREEN.
- S5 #25 / `35613663393` on HEAD `7825318366afd68430d511a15ce06f739c2b7f14` ended CANCELLED with no artifact, so it contributes no market-negative conclusion.
- First-Hunt #69 on HEAD `7825318366afd68430d511a15ce06f739c2b7f14` remains the latest bounded complete current-head hunt with 1,280 observations and no positive gross/post-flash result.
- Safety locks remain unchanged: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • TREE REPAIR + S5 V4

- Canonical current branch state was verified against live GitHub, not chat memory.
- Pre-incident canonical HEAD: `b6be20f3764b58260ce1114be09052f6c04d52ff`, full tree 338 entries.
- Intermediate commit `68a52cc0...` was a partial-tree control-plane error and is not admissible project state or market evidence.
- Repair `aadf4979...` restored the full 338-entry tree; only the intended S5 workflow and kick differed from `b6be20f...`.
- Read-only First-Hunt #70 completed 36/36 declared tiles with 1,280 observations, zero gross-positive/post-flash-positive at block `94204969`; no EconomicProof or profit claim.
- Historical crawler #115 completed slice 400000-499999 with next cursor 500000, but all six venues were ONCHAIN_UNAVAILABLE; do not interpret that as no-pool evidence.
- Clean S5 kick-only commit `dc2deb28...` changed only `.github/PHANTOMX_S5_KICK`; S5 timeout is 60 minutes.
- Phase-19 #1023 is GREEN on `dc2deb28...`. S5 #29 / `35635495324` is active on that exact HEAD.
- Evidence record: `PHANTOMX_CONTROL_PLANE_TREE_REPAIR_EVIDENCE_2026-09-21.md`.
- Production remains locked: LIVE SIGNING BLOCKED; PUBLIC BROADCAST BLOCKED; LIVE CAPITAL LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • BOUNDED RPC ADMISSION REPAIR

- Verified engineering HEAD: 3e84ff7e2ce2cb83701729a79c62a3f6dd9a03ca.
- S5 #42 forensic finding: complete tile/evaluation accounting existed, but 6,002 evaluations produced a zero-attempt bounded-RPC exhaustion message caused by temporary provider-slot saturation under concurrent tile execution.
- Surgical repair adds bounded provider admission waiting without increasing provider concurrency or allowing unbounded retry/fan-out.
- Phase-19 #1067 / run 35854419968 is GREEN on the repair HEAD.
- A fresh S5 controlled kick from this verified HEAD is the immediate next market action.
- No profitability, EconomicProof, or production authorization is inferred.
- Safety locks remain: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.
