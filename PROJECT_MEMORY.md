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

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 #44 PROVIDER-POISONING FORENSIC REPAIR

- S5 #44 / run 35863910575 on HEAD c2d93c28ee58c553516b0d067c5476069ebb4183 is terminal FAILURE with published artifact 10751961217.
- Artifact: 164/164 tiles accounted; 3 complete; 161 incomplete; pair surface COMPLETE_RECENT_WINDOW; 5,636 retryable evaluations; 76 observations; 0 gross-positive; best gross -4.452314 USDC; economic_certification=NOT_PERFORMED; profit_claim=NONE.
- Provider-diversity repair is verified as functioning; remaining dominant failure classes are provider-local 429/rate-limit and historical-state/capability failures.
- Surgical repair adds 60-second temporary provider quarantine for those local conditions, while retaining long quarantine for authentication/paid-plan failures.
- No search-domain, loan-frontier, concurrency-limit, retry-envelope, economics, signing, broadcast or capital change.
- Exact-head Phase-19 #1070 / 35863910697 is GREEN on the pre-repair HEAD; post-repair verification is required before a fresh market hunt.
- S0 remains blocked behind complete S5 evidence.
- data-plane-ci absent and not GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 #45 FRESH GENERATION LAUNCHED

- Post-repair deterministic verification is complete: Phase-19 #1071 / run 35866369537 is terminal SUCCESS on exact engineering HEAD caae9895cabbbf1a93bc6112f4475842cb852f7b. Compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe and the full unittest suite are GREEN.
- S5 #44 / run 35863910575 is terminal FAILURE with artifact 10751961217. Its 164-tile scan produced 76 observations, 0 gross-positive observations and best gross -4.452314 USDC, but coverage was incomplete: 3 complete and 161 incomplete tiles with 5,636 retryable failures. economic_certification=NOT_PERFORMED and profit_claim=NONE. This is not a complete market certificate.
- The #44 forensic repair added bounded 60-second provider-local quarantine for rate-limit/service-unavailable and historical-state/pruned provider failures while preserving distinct-provider failover, per-provider concurrency, bounded recovery, search domain, loan frontier and economic gates.
- Controlled S5 #45 has now been triggered from the exact verified post-repair lineage through .github/PHANTOMX_S5_KICK.
- S5 #45 is the sole active market-hunt lane; no overlapping S5 generation is authorized.
- S0 remains blocked until S5 produces terminal, complete declared-domain evidence and passes the separate economic certification gate.
- data-plane-ci is absent and is not reported as GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## S5 #45 RPC REPAIR VERIFIED • 2026-09-23
The ambiguous-revert/provider-reuse repair is committed at the verified HEAD and Phase-19 #1073 is GREEN. The next controlled action is a single fresh S5 read-only evidence run on this exact lineage. S5 certification remains blocked until coverage is complete.


## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 #46 FORENSIC CLASSIFICATION PARITY
- S5 #46 / run 35875307284 on exact HEAD `acf96579c03ef05dcc1457ac66573e3fc8f50b09` is terminal FAILURE with artifact `10759348462` (ZIP SHA256 `520478e6d1dc2d292d38535177fe1ce5993fe65ee02e212adc4766ed9756ff40`).
- Artifact forensic result: 164 tiles accounted; 14 COMPLETE + 2 COMPLETE_NO_COMMON_ROUTE = 16 complete; 148 incomplete; 532 observations; 0 gross-positive; best gross `-$4.452314` USDC; pair universe `COMPLETE_RECENT_WINDOW`; economic_certification=`NOT_PERFORMED`; profit_claim=`NONE`.
- The scan recorded 1,319 retryable and 4,288 terminal failures. This is incomplete infrastructure evidence, not market-negative evidence.
- Root cause isolated for the surgical next repair: `RPCSemanticRevertConsensusError` is terminal in OpportunityDiscovery but its message was missing from the S5 tile classifier terminal-marker set. One 38/38 terminal-consensus tile was therefore misclassified PARTIAL_INCOMPLETE; `execution reverted: SPL` also lacked explicit parity.
- Repair is limited to S5 classification parity plus deterministic regression tests. Remaining retryable RPC failures are deliberately left unresolved for separate evidence.
- Dedicated forensic record: `PHANTOMX_S5_46_FORENSIC_CLASSIFICATION_REPAIR_2026-09-23.md`.
- S0 remains blocked until S5 complete declared-domain evidence is certified.
- data-plane-ci remains absent and is not GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 CLASSIFICATION PARITY VERIFIED
- Surgical S5 tile-classification parity repair is committed at `ae31dced5aefe3bceb4ca9a29c531c486bcf1155`.
- Exact-head Phase-19 #1075 / run `35881949251` is terminal SUCCESS.
- Fresh S5 current-head evidence is now triggered from this verified repair lineage through `.github/PHANTOMX_S5_KICK` using kick `2026-09-23-s5-classification-parity-v22`.
- Next admissible gate: S5 terminal artifact -> coverage forensic -> isolate remaining retryable RPC failures -> certify or apply one surgical repair.
- S0 remains blocked until S5 complete declared-domain evidence is certified.
- data-plane-ci remains absent and is not GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.
## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 #47 AMBIGUOUS-REVERT PROVIDER-HEALTH ROOT CAUSE
- S5 #47 / run 35882243231 on exact HEAD 183785170bdd7f96f2fc23d61eca557c1c754bb2 is terminal FAILURE with artifact 10762506820 (ZIP SHA256 945fb591777ad0d4991e681749f85dba03927f35cf7b926ab28c7f3e3b301f61).
- Artifact: 164 tiles accounted; 30 complete (14 COMPLETE + 16 COMPLETE_NO_COMMON_ROUTE), 134 incomplete, 532 observations, 0 gross-positive, best gross -$4.452314 USDC, pair universe COMPLETE_RECENT_WINDOW.
- Retryable failures: 1,339; terminal failures: 4,266. This is incomplete infrastructure evidence, not market-negative evidence.
- Root cause isolated: ambiguous semantic execution reverts were being treated as recoverable provider-health failures, opening circuits/degrading health under concurrent S5 load and causing many single-provider recovery-exhaustion diagnostics.
- Forensic slice: 1,194 retryable failures contain a single-provider generic execution reverted diagnostic. This is the target of the surgical repair.
- Repair: ambiguous semantic reverts are now recorded for evidence but do not poison provider health/circuit state; they remain excluded only from the current bounded logical recovery pass and still require two distinct-provider consensus before terminal classification.
- Dedicated forensic record: PHANTOMX_S5_47_FORENSIC_RPC_HEALTH_REPAIR_2026-09-23.md.
- S0 remains blocked until S5 complete declared-domain evidence is certified.
- data-plane-ci remains absent and is not GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 RPC-HEALTH REPAIR VERIFIED
- Repair commit `ceef15274b8c0765ad81383af054742bd116b51b` is the current engineering HEAD.
- Phase-19 deterministic tests on this exact HEAD are GREEN (`35886670918`).
- The verified repair prevents ambiguous reason-less reverts from degrading provider health/circuit state; consensus semantics and fail-closed coverage remain unchanged.
- Fresh S5 trigger is committed through `.github/PHANTOMX_S5_KICK` as `2026-09-23-s5-rpc-health-repair-v23`.
- Next admissible gate: fresh S5 terminal artifact -> coverage forensic -> retryable-failure comparison against #47 -> certification or one surgical repair.
- S0 remains blocked until S5 complete declared-domain evidence is certified.
- data-plane-ci remains absent and is not GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 #48 FORENSIC + RPC CAPACITY REPAIR
- S5 #48 / run `35888656857` on `f645f6ce7bf0e14784437970cb3a758e4590b289` is terminal FAILURE with artifact `10765085719`.
- Coverage improved materially versus #47: 45/164 terminal-complete tiles, 119 incomplete; retryable evaluations fell from 1,339 to 344. This remains incomplete evidence, not market-negative evidence.
- Dominant residual: 257 single-provider ambiguous reason-less reverts became retryable because the remaining provider fleet was unavailable or quarantined at that instant.
- Surgical repair pushed now: current official public QuickNode lane replaces deprecated keyless `polygon-rpc.com`; historical-state errors are task-local instead of provider-wide temporary quarantine. Regression coverage added.
- Fresh S5 kick is now `2026-09-23-s5-rpc-capacity-repair-v24` on the repaired current HEAD.
- S0 remains blocked until S5 produces complete declared-domain evidence and passes the separate economic-certification gate.
- data-plane-ci remains absent and is not GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 #49 WORKFLOW-CHECK REPAIR
- S5 #49 / run `35894615418` did not execute market scanning: exact-head verification failed because the newly added S5 workflow contained literal escaped shell variables.
- No S5 market evidence was produced from #49; no coverage or market conclusion is inferred.
- Surgical workflow correction is now pushed: shell variables are restored to runtime expansion semantics, and a fresh S5 kick v25 is included in the same repair push.
- S0 remains blocked. LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • RPC REPAIR CI CORRECTION
- Phase-19 #1082 on `00f84b50...` exposed two self-inflicted regression assertions in the new RPC capacity repair: missing public-pool import in the test and historical-state quarantine behavior not yet removed from the implementation.
- These are now surgically corrected. No scanner, strategy, economic, signer, broadcast, or capital semantics are changed.
- No new S5 hunt is kicked until the exact repair HEAD receives GREEN Phase-19 verification.
- S0 remains blocked until S5 complete declared-domain evidence is certified.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 RPC SCARCITY RETRY TEST CLEANUP
- Current HEAD before this repair: b8dcd311e582ac3721bccdc43b2d53bd89e61c2f.
- Phase-19 #1085 failed one registry assertion only: the test required QuickNode, while the current active zero-cost pool does not include it. The implementation itself and all other 943 tests were successful.
- The test is now bound to the actual declared free-provider registry, while preserving the removal of the deprecated polygon-rpc.com entry.
- A bounded delayed same-provider retry is now implemented and regression-tested for one ambiguous reason-less revert when no alternate provider is currently usable.
- Fresh S5 kick will follow the GREEN exact-head verification of this repair.
- S0 remains blocked until S5 complete declared-domain evidence is certified.
- data-plane-ci remains absent and is not GREEN.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.
