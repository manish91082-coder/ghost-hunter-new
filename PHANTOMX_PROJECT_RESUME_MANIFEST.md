# PHANTOMX PROJECT RESUME MANIFEST

**Machine-readable continuity anchor for any future ChatGPT/AI/operator.**

## Identity

- Repository: `manish91082-coder/ghost-hunter-new`
- Canonical branch: `phase-19-e2e-harness`
- Base branch: `master`
- Project: PHANTOMX / Flash Loan Ghost Hunter
- Primary chain: Polygon PoS Mainnet, chain ID 137
- Current canonical flash-liquidity source: Aave V3
- Current canonical venues: QuickSwap V2 and Uniswap V3
- Current canonical route family: direct two-leg A -> B -> A
- Current production execution: BLOCKED
- Live capital: LOCKED

## Immutable mission

`LIVE MARKET -> EXACT ROUTE -> DYNAMIC LIQUIDITY/LOAN -> EXACT GAS -> ALL COSTS -> CONSERVATIVE NET > $0.20 -> FINAL REQUOTE -> EVM PREFLIGHT -> GOVERNOR -> CONTROLLED SIGNER -> PRIVATE SUBMIT -> RECEIPT -> INDEPENDENT REALIZED PNL > $0.20 -> FINAL AUDIT -> FREEZE`

Do not freeze winning market parameters. Freeze the economic/safety protocol and keep market parameters dynamic.

## Current market search

- Exploratory pairs currently configured: USDC/WETH, USDC/WPOL, USDC/WBTC, USDC/DAI, USDC/LINK, USDC/AAVE, USDC/UNI.
- Uniswap V3 fee tiers searched: 100, 500, 3000, 10000.
- Discovery loan frontier: explicit amounts used for bounded search; production loan sizing must be derived from live Aave liquidity plus venue executability and route-impact constraints.
- Route directions: QuickSwap V2 -> Uniswap V3 and Uniswap V3 -> QuickSwap V2.
- Gross-positive observations are NOT profitability certificates.

## Dynamic principles

### Gas
Gas is transaction-level. Never model gas as a percentage of loan amount.
Use exact execution-path gas estimation/preflight and actual receipt gasUsed/effective gas price for realized reconciliation.

### Loan sizing
`L_max = min(Aave_available, venue_executable, route_impact_bound, repayment_safe, explicit risk bound)`.
Aave liquidity alone is never sufficient.
Fixed loan grids are only search aids.

### Flash fee
Read the actual Aave Polygon Pool premium at the pinned/finalized observation boundary. Do not hardcode a universal flash-fee percentage.

### RPC fleet
Maintain a large replaceable registry. Do not broadcast every task to hundreds of RPCs.
Use bounded active selection, health scoring, rate limits, circuit breakers, task chunking, block pinning, and rotation/failover.
Provider diversity is for quorum/evidence and resilience, not indiscriminate fan-out.

## Current deterministic spine

`BLOCK -> RPC/QUORUM -> EXACT QUOTES -> ROUTE -> LOAN BOUNDS -> COSTS -> ECONOMIC PROOF -> FINAL REQUOTE -> PREFLIGHT -> GOVERNOR -> SIGNER -> PRIVATE RELAY -> EXECUTION -> RECEIPT -> REALIZED PNL`

AI may rank and prioritize. AI cannot override deterministic quote/economic/preflight/governance/settlement gates.

## Current strategy registry

### Canonical
- S0-DIRECT-QS-V3: QuickSwap V2 <-> Uniswap V3 direct two-leg.

### Discovery-only
- S1-QS-V3
- S2-UV4-V3
- S3-RAMSES-UV3
- S4-BALANCER-UV3
- S5-CURVE-UV3
- S6-TRIANGULAR
- S7-STABLE-STABLE
- S8-ALTERNATIVE-FLASH-LIQUIDITY

Discovery-only strategies never authorize production execution. Each requires adapter provenance, exact quote coverage, economic proof, adversarial tests, fork evidence and production authority review before promotion.

## Current milestone evidence

- Phase-19 deterministic baseline: Run #596 at the latest verified code path is GREEN after the bounded RPC scheduler factory fix.
- First-Hunt #16: GREEN after dynamic route-bound optimization; exact live observations were produced without signing/broadcast.
- First-Hunt #18 is the current active-head hunt when this manifest is regenerated; verify its latest conclusion from GitHub Actions before treating it as current market evidence.
- Historical First-Hunt #14: 920 observations per successful RPC, zero gross-positive; best gross approximately -$0.121905.
- Historical First-Hunt #11: 1,292 exact observations across two successful providers, zero gross-positive.
- Any Actions result from an older commit must not be treated as evidence for a newer HEAD unless the relevant files are unchanged and the run is explicitly proven applicable.

## Wallet / signer security

- Public deployment/deployer identity may exist in historical evidence files. It is not production authority by itself.
- Private key material must never be stored in repository files, fixtures, logs or chat.
- Canonical signer proof is verifier-only: generate a fresh challenge, obtain an external signature, recover the signer address, and bind the result to current production-authority evidence.
- `scripts/verify_signer_identity.py` must never receive a private key.
- `scripts/validate_signer_evidence.py` validates the non-secret evidence package.
- Live signer authorization remains BLOCKED until fresh external signer evidence is accepted.

## One-click operator model

The project must expose one operator entrypoint that dispatches deterministic reusable workflows for:

1. AUDIT
2. TEST
3. LIVE-HUNT
4. PREPARE-STAGING
5. STAGING
6. PRODUCTION-READY-CHECK
7. LIVE-EXECUTION (only after every external production gate is green)

A single click is an orchestration interface, not a safety bypass.

Recommended GitHub design:
- `workflow_dispatch` top-level operator workflow
- reusable workflows for repeatable deterministic stages
- environment protection for staging/production
- environment secrets only at the protected stage
- concurrency = 1 for production execution
- explicit prerequisite checks before each stage
- all stage artifacts persisted for audit and handoff
- live stage must fail closed if signer, RPC authority, relay, artifact identity or economic proof gates are absent.

GitHub supports manually dispatched workflows, reusable workflows, deployment environments with protection/approval, environment-scoped secrets, and concurrency controls. See official docs linked below.

## Cross-AI continuity protocol

This repository is the durable project memory.

Every substantive cycle must update:
- `PHANTOMX_PROJECT_RESUME_MANIFEST.md`
- `PROJECT_STATUS.md`
- relevant strategy/economic/security documents
- evidence artifacts when produced

Each update should record:
- current HEAD
- current branch
- last verified GREEN commit/run
- current active gate
- newly proven facts
- newly discovered blockers
- next deterministic action
- forbidden assumptions
- external evidence state

A future AI should read this manifest first, then `PROJECT_STATUS.md`, then the latest relevant Actions run, then the relevant code/tests.

Never use chat memory as the sole project source of truth.

## No-drift rule

Before any repository write:
1. verify repository identity;
2. verify branch;
3. read this manifest;
4. read `PROJECT_STATUS.md`;
5. inspect current HEAD;
6. inspect latest relevant Actions/PR/Issue;
7. identify one unresolved bottleneck;
8. write only the minimum substantive change;
9. verify exact-head CI evidence;
10. update the manifest and status.

Never steer based on a different repository, stale branch, stale run, or historical status file.

## External production gates

LIVE SIGNING = BLOCKED
PUBLIC BROADCAST = BLOCKED
LIVE CAPITAL = LOCKED

Required independent lanes:
A. Polygon production authority
B. production signer
C. private relay
D. identical-artifact shadow/staging
E. realized economics / PnL

Missing lane = BLOCKED.

## GitHub official references

- Manual workflow dispatch: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
- Reusable workflows: https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations
- Environments and required reviewers: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Environment management: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- Secrets reference: https://docs.github.com/en/actions/reference/security/secrets
- Workflow artifacts: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts

## Resume instruction

**Next AI action:** do not add another discovery dimension blindly. First reconcile current First-Hunt evidence, then integrate exact execution-path gas and live valuation into the existing `EconomicProof` boundary. After that, build the one-click operator workflow around reusable deterministic stages. Only then promote additional strategies through the registry.


## Latest control-plane sync
- Current branch HEAD at sync: `fc9d181e37302d81cb7bb363d93f8580e203ad6a`.ne-click operator workflow: `.github/workflows/phantomx-one-click.yml`.
- Latest applicable Phase-19 regression: run `#596`, GREEN on `b19c8c08...`.
- Latest applicable First-Hunt market evidence: run `#18`, GREEN on `b19c8c08...`; operator-only commits after that do not change the scanner inputs.
- Private key: not tracked in current branch. Production signer identity remains an external evidence gate.

## DYN-3 LATEST SYNC
- Current HEAD: `0ecc1a06b7101e6b19d0785a8c5d2d234e378328`.
- Exact gas observation: `phantomx/gas_observation.py`.
- RPC read surface expanded only for `eth_estimateGas`, `eth_gasPrice`, and `eth_maxPriorityFeePerGas`; send/broadcast methods remain blocked.
- DYN-3 remains observation-only until live valuation and EconomicProof binding are complete.

## DYN-3 VERIFIED
- Phase-19 run #606 / ID `35347563215` is GREEN on current engineering head `fc9d181e...`.
- Gas observation is read-only and block-pinned; gas USD conversion requires explicit valuation evidence.
- Current First-Hunt #21 is on older head `0aef20...` and is not current-head evidence.

## DYN-4 VERIFIED
- Current HEAD: `59f1e88fd841e2e91a427eaca0329960dd759ac4`.
- Phase-19 #615 / ID `35350779558` GREEN.
- DYN-4 economic binding preserves exact quote settlement semantics and adds only external attributable costs: flash-loan premium, gas, relay and other explicit costs.
- Next gate: DYN-5 final requote/state lock.

## DYN-5 VERIFIED
- Current engineering head: `97174b5e337dfb906b55984461396f3e9b34712c`.
- Phase-19 #617 / ID `35356389228` GREEN.
- Final state lock requires exact current-block alignment and fresh route/quote/economic evidence; stale or below-floor final proofs cannot be locked.
- First-Hunt #24 / ID `35356389245` is currently the active current-head read-only market scan; do not treat it as complete until its final conclusion/evidence is captured.

## S1 AUTOMATION SYNC
- Current branch head before this automation commit: `478b2de5d076605c3d102d4b75fe9017d6599caf`.
- Dedicated S1 live-read workflow added: `.github/workflows/s1-qsv3-live-read.yml`.
- The workflow is read-only, cancels stale S1 hunts, and archives `artifacts/s1_qsv3_live_scan.json`.
- S1 remains discovery-only and cannot authorize production execution.

## LATEST AUTOMATION CONTROL SYNC
- Current control HEAD: `617e203e0033e5a1589b6fa1c71bf29fecbf0053`.
- Phase-19 #630 / ID `35364653977` GREEN.
- S0 live-hunt #29 on `b6f291f6...` completed GREEN with zero gross-positive; use only as applicable scanner evidence until quote/economic head changes.
- S1 dedicated automated hunt #3 on `b6f291f6...` remains in-flight; the latest trigger-cleanup change was not a scanner-code change.


## CURRENT HEAD RECONCILIATION — 2026-09-18

- GitHub branch API independently verified canonical branch `phase-19-e2e-harness` at HEAD `6a399d4f245f22b598ec70d5c35ae853dba4ef81`.
- Latest exact-HEAD Phase-19 run: #631 / ID `35364977680`, GREEN, triggered by push to HEAD.
- The prior status/manifest anchors referencing `b19c8c08...` and `617e203e...` are historical snapshots, not current branch HEAD.
- Certification PR #1 remains OPEN; its head SHA now matches current branch HEAD.

### S1 live evidence
- Dedicated S1 run #3 / ID `35364241167` completed GREEN on scanner head `b6f291f6da90bd688b83cd95c717ea1e670b714c`.
- Comparison `b6f291f6...` -> current HEAD `6a399d4...` contains only workflow/control-plane and status/manifest changes; no S1 scanner, adapter, route, dynamic-policy or strategy-registry files changed.
- Artifact `phantomx-s1-qsv3-live-scan` was independently retrieved from run #3.
- S1 evidence: 3 provider attempts; DRPC produced 800 observations, PublicNode produced 560 observations, 1RPC returned zero route observations; total exact route observations = 1,360; gross-positive = 0.
- Best observed gross result: `-$0.006883` USDC on PublicNode at block `94027615`; DRPC best was `-$0.007176` at block `94027535`.
- Aave dynamic evidence: available USDC liquidity `611558.815434`, dynamic ceiling `580980.874662`, flash premium `5 bps`; the same Aave pool identity was observed by all successful endpoints.
- QuickSwap V3 fee is quote-derived in the scanner; observed route legs recorded dynamic fee data (example: QuickSwap V3 fee `10` raw units and Uniswap V3 tier `100`).
- S1 artifact explicitly reports `economic_certification=NOT_PERFORMED` and `profit_claim=NONE`. Therefore S1 is live-discovery VERIFIED, but EconomicProof / exact gas / native valuation / final state-lock certification is NOT achieved.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.


## CURRENT VERIFIED SYNC • 2026-09-20

- Canonical HEAD: `810b190e3660394bc3be2923d3dc01f958457e57`.
- Latest completed Phase-19 certification: run `#871` / `35505502629`, GREEN, **878 tests** on parent `9b3fd466...`. Current post-gate verification run #872 is active on HEAD `810b190e...`.
- Latest completed First-Hunt: #44 / `35505502646`, GREEN as a read-only scan with **1,216 observations**, 0 gross-positive and 0 post-flash-positive; best gross `-$0.122095`; best post-flash `-$0.172095`; block `94130318`.
- The #44 scan covered 32/36 pair/fee tiles. Four tiles were unresolved, so this is **not** exhaustion proof.
- Current First-Hunt #45 is running on `810b190e...` with fail-closed coverage semantics.
- Historical Universe Crawler #5 completed only the first `0-99999` slice to fixed snapshot `94129645`; automatic continuation was disabled. Historical universe exhaustion remains open.
- Live signing, public broadcast and live capital remain blocked/locked.

## CURRENT AUTHORITATIVE SYNC • 2026-09-20 • LATEST

- Canonical branch HEAD: `a3fda4b0ce4c3090f06a5db059bb106bd7946efb` after status synchronization.
- Historical campaign is immutable: campaign `polygon-genesis-94135487`, snapshot `94135487`, campaign commit `68b35b09441d9d7f3b64530096114fb66eb78938`.
- Certified genesis slice: run `#12`, `0-99999`, next resume `100000`.
- History crawler orchestration is now single-flight and canonical-locked. It triggers only through the dedicated history-kick sentinel or manual workflow dispatch.
- Legacy race-created campaigns are explicitly non-canonical and rejected by resolver validation.
- Current completed Phase-19 remains GREEN through run `#899`; the latest push has an active verification run.
- Broad current-head S0 proof is still missing. No strict `net > $0.20` EconomicProof or realized PnL exists.
- S10 gross-positive observations remain below flash-premium economics; do not promote them.
- Next deterministic priority: let canonical historical crawler resume from block `100000`, while keeping the discovery/economic gates fail-closed. Then reconcile fresh current-head S0 evidence before any execution-bound promotion.

## CURRENT AUTHORITATIVE SYNC • 2026-09-20 • POST-RESUME KICK

- Current HEAD after documentation sync will be the commit immediately following `af4f6dc4ef007c503cef01c078e92e98a931ec3a`.
- Phase-19 run `#902` / `35513839907` is GREEN on `af4f6dc4...`.
- Historical crawler #27 is the active canonical campaign run: snapshot `94135487`, resume `100000-199999`, campaign commit `68b35b09441d9d7f3b64530096114fb66eb78938`.
- Six venue inventory lanes are active for the canonical slice. Certification is pending until all declared venue evidence passes.
- The canonical history workflow is single-flight, canonical-locked, and only kickable through the dedicated sentinel or explicit manual dispatch. Ordinary code changes do not start a new campaign.
- No current-head broad S0 profitability certificate exists. Live signing, public broadcast and live capital remain blocked/locked.


## CURRENT AUTHORITATIVE SYNC • 2026-09-20 • HEAD 00547

- Current HEAD: `00547b3c22d49dd21b0cb5c48c0c2b7b99b84cfb`.
- Phase-19 #905 is GREEN on current HEAD.
- Canonical historical inventory campaign is locked to snapshot `94135487`. Certified contiguous coverage: `0-99999`, `100000-199999`; active next slice: `200000-299999`.
- S0 First-Hunt #53 is running on `625f6385...`; it is the first clean broad hunt after discovery retry/coverage corrections.
- No current-head profitable certificate exists. Gross-positive observations from S10 are below the flash-premium floor and have not reached gas/economic/final-lock stages.
- Production execution gates remain blocked until a current genuine candidate passes complete EconomicProof, exact final gas/valuation, final requote/state lock, external authority/signer/relay/shadow gates, and realized PnL > $0.20.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • REPOSITORY DRIFT + CLEANUP AUDIT

- Canonical branch remains `phase-19-e2e-harness`; the canonical PHANTOMX MVP architecture remains aligned with the immutable mission spine in this manifest.
- Latest semantic-revert coverage repair remains:
  - `014e14ed25859a80d0f057c3e6de76adac1d4cb3` discovery-layer terminal classification fix.
  - `864f45b9418cf019bd4f6ab1acda4bb2bd565f21` regression tests for semantic revert versus transport retry behavior.
- First-Hunt #67 / run ID `35536094045` is incomplete: 30 jobs, 26 successful, 4 failed. No complete 36-cell market certificate exists.
- Repository cleanup audit `PHANTOMX_REPOSITORY_CLEANUP_AUDIT_2026-09-21.md` inspected the canonical branch inventory and found **zero files proven unrelated**. Therefore **zero files were deleted**.
- The canonical branch contains 282 tracked files in the focused PHANTOMX tree. Legacy `v2/`, `v3/`, `agents/`, `common/`, notebook and training material observed on the `master` baseline are not present in the canonical branch and were deliberately not touched.
- Control-room helper documents were retained because their contents directly describe Phase-19 safety/coordination validation. They are related audit material, even where overlapping in wording.
- A documentation-drift finding was corrected: this manifest had lagged behind the 2026-09-21 semantic-revert repair. This section is now the authoritative current sync; older sections remain historical records.
- No architecture drift was found against `PROJECT_DETAILS.md`, `PHANTOMX_POLYGON_ARBITRAGE_STRATEGY_CATALOG.md`, `PHANTOMX_POLYGON_WIDE_HUNT_PLAN.md`, and the safety gates.
- Safety remains unchanged: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.
- Next execution priority remains CI verification of the semantic-revert repair, followed by a fresh isolated 36-cell First-Hunt only after verification.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • EXACT-HEAD RECONCILIATION AFTER FRESH FIRST-HUNT KICK

- Canonical repository and branch were independently re-verified: `manish91082-coder/ghost-hunter-new` / `phase-19-e2e-harness`.
- Branch HEAD immediately before this documentation synchronization was `a9cb6aca4fd3be5ca4d2c424d89f388cecbe46e4`, created solely by updating the existing `.github/PHANTOMX_FIRST_HUNT_KICK` sentinel to trigger a fresh controlled read-only hunt.
- Exact-head Phase-19 run #953 / ID `35566476152` completed **successfully** on `a9cb6aca...`. The prior Phase-19 run #952 on `3cfc43ee...` also completed successfully. The exact-head verification therefore now exists for the repair + cleanup-trigger lineage.
- Fresh First-Hunt #68 / ID `35566476146` was successfully created by the dedicated kick sentinel and is running/queued against exact HEAD `a9cb6aca...`; no market result or exhaustion claim is made until its aggregate evidence is complete.
- The First-Hunt workflow remains a 36-cell matrix: 4 fee tiers × 9 pair indices, with fail-closed aggregation and no signing, submission, broadcast, or live capital.
- Current tree at the reconciled engineering state contains **318 tracked files** across `.github/`, `contracts/`, `phantomx/`, `scripts/`, and `tests/`. Earlier 282-file statements in historical cleanup/status sections are historical checkpoints and are not the current inventory.
- The two surgical deletions previously proven safe remain intact: `scripts/README.tmp` and `tests/phase19/test_control_room_validator.tmp`. Their deletion commits are preserved as audit evidence.
- No architecture drift was found. Legacy `master` material remains outside the canonical branch and was not modified.
- Market profitability remains unproven. No strict `net > $0.20` EconomicProof, realized PnL certificate, or production authorization exists.
- **LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.**


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • FIRST-HUNT #68 TERMINAL AGGREGATE

- First-Hunt `#68` / run `35566476146` completed successfully on `a9cb6aca4fd3be5ca4d2c424d89f388cecbe46e4`.
- Complete GitHub Actions enumeration returned **38 jobs** = 1 resolver + **36/36 shards** + 1 aggregate. The earlier 30-job view was a first-page result, not incomplete coverage.
- Aggregate artifact `phantomx-first-hunt-live-scan` / ID `10623829992` has SHA-256 `eb835ba941814ae3ad360cf228837c6e34f2dafe2e8a1dc1de546a17c30c7a9c`.
- Coverage certificate: **36/36 complete**, 0 incomplete, 0 missing. Four tiles are `COMPLETE_NO_COMMON_ROUTE`: USDC/WBTC at fee 100, USDC/LINK at fee 100, USDC/UNI at fee 100, and USDC/AAVE at fee 500. The other 32 tiles completed with route observations.
- Market block = **94176798**, chain ID = **137**, with one pinned block across the aggregate.
- Aggregate observations = **1,246**; gross-positive = **0**; post-flash-positive = **0**; best gross = **-$0.115879**; best post-flash = **-$0.165879**.
- The artifact explicitly states `economic_certification=NOT_PERFORMED` and `profit_claim=NONE`. This is complete coverage for the declared First-Hunt domain, not a profitability or Polygon-wide exhaustion certificate.
- Current branch HEAD is `e646c1d57bf4d52f78a36c98fd7b68469a129892`. Comparison from hunt commit `a9cb6aca...` shows only the continuity/status documents changed after the hunt trigger.
- Production gates remain blocked/locked.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • FIRST-HUNT #68 TERMINAL
- First-Hunt #68 / `35566476146` completed successfully on exact hunt HEAD `a9cb6aca4fd3be5ca4d2c424d89f388cecbe46e4`.
- Coverage certificate: **36/36 cells complete**, 36/36 shards accounted, 0 incomplete, 0 missing, 0 rejected.
- Tile outcomes: 32 `COMPLETE`, 4 `COMPLETE_NO_COMMON_ROUTE`.
- Exact route observations: **1,246**.
- Gross-positive: **0**. Post-flash-positive: **0**.
- Pinned Polygon block: **94,176,798**.
- Best gross observation: **-$0.115879 USDC**. Best post-flash observation: **-$0.165879 USDC**.
- The hunt artifact explicitly records `economic_certification=NOT_PERFORMED` and `profit_claim=NONE`. Therefore this is bounded complete-discovery coverage evidence, not profitability proof and not Polygon-wide exhaustion proof.
- Exact execution gas, native/USD valuation, relay/MEV cost, final requote/state lock, EVM preflight, Governor, external production authority, signer, private relay, shadow/staging, controlled execution, receipt reconciliation and realized PnL remain separate gates.
- **LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.**

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

- Canonical branch HEAD: `3ea4d347f1d400232342f5f44c93a5a9948e93c8`.
- S3 #17 / `35578078265` was workflow-successful but artifact coverage was **168/168 UNAVAILABLE_OR_FAILED**: 164 deterministic missing Ramses pools, 4 RPC semantic reverts. This is not complete coverage evidence.
- Repair `0213dea08fffbc30256ded62dd5b91c28b605936` now fail-closes unresolved S3 coverage, records explicit `COMPLETE_NO_COMMON_ROUTE` versus `PARTIAL_INCOMPLETE`, and returns non-zero on incomplete aggregate coverage.
- Regression matrix `3ea4d347f1d400232342f5f44c93a5a9948e93c8` is verified by Phase-19 #982 / `35580051618` GREEN with 899 tests.
- S3 verification run #18 / `35579964402` is active on the repair commit. No S3 conclusion is admissible until its terminal artifact is inspected.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 RUN #19 + RPC AMBIGUOUS-REVERT REPAIR

- S3 #19 artifact `10629758616` preserved evidence: 164/168 terminal no-route, 4/168 incomplete, 0 observations; aggregate `PARTIAL_INCOMPLETE`.
- The four unresolved cells are USDC.e/DAI at Ramses tickSpacing 1 across all four declared Uniswap fee tiers, all with uninformative `execution reverted: Unexpected error`.
- Commit `f499920edb177680c04d0bd7ce3749af131394dd` introduces bounded failover for this ambiguous provider response only; regression commit `ba4d347c9d5fe9471aab06cdbe8797ac358f7146` is Phase-19 verified.
- Next gate is current-head S3 live verification after the RPC repair.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • CANONICAL RPC REPAIR REAPPLIED

- Do not infer file content from parent ancestry alone. Current branch tree content is authoritative.
- The ambiguous-RPC repair is being reapplied directly from canonical HEAD and must be verified again before the S3 lane can advance.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 #23 COMPLETE

- Current HEAD: `4028cdd375b3455b2d4b3972506b669058d9e6f6`.
- S3 #23 / `35595059504` is complete on the declared 168-cell matrix: 168/168 covered, 0 incomplete, 160 observations, 0 gross-positive, best gross `-$0.009175`, best post-flash `-$0.059175`.
- 164 cells are terminal `COMPLETE_NO_COMMON_ROUTE`; 4 cells have common routes and were quoted successfully.
- Artifact: `10636560576`; GitHub digest `sha256:7f9483318d3d605abb8a2c2924172bc3ab8140328e1bf6da3dee112673d60aca`.
- This is complete bounded S3 evidence only. Polygon-wide universe exhaustion and strict `net > $0.20` profitability remain unproven.
- Next frozen expansion lane: S5 Curve ↔ Uniswap V3, subject to current workflow/evidence inspection.


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

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • LIVE TREE REPAIR / S5 CURRENT-HEAD

- Live GitHub branch `phase-19-e2e-harness` was reconciled directly. Do not trust older HEAD values in this manifest over `PROJECT_STATUS.md`.
- Tree-integrity incident: `68a52cc0...` was an invalid partial-tree intermediate commit. S5 #28 failed before scanning because `requirements-phase19.txt` disappeared from the tree. No market evidence was accepted.
- Canonical repair: `aadf4979...`; verified full tree 338 entries and only intended S5 workflow/kick modifications versus `b6be20f...`.
- First-Hunt #70: 36/36 complete, 1,280 observations, 0 gross-positive, 0 post-flash-positive, block `94204969`; bounded discovery evidence only.
- Historical #115: canonical campaign `polygon-genesis-94135487`, slice 400000-499999, next cursor 500000; all six venues ONCHAIN_UNAVAILABLE, so historical availability remains unresolved for that slice.
- Clean current S5 head: `dc2deb28...`; only `.github/PHANTOMX_S5_KICK` changed from repaired tree; S5 timeout 60 minutes.
- Phase-19 #1023 GREEN. S5 #29 / ID `35635495324` active on `dc2deb28...`.
- Dedicated incident evidence: `PHANTOMX_CONTROL_PLANE_TREE_REPAIR_EVIDENCE_2026-09-21.md`.
- Safety invariant unchanged: LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.
- Next gate is S5 #29 terminal artifact inspection. Never promote read-only scan output directly to execution authorization.

## CURRENT AUTHORITATIVE SYNC • 2026-09-23 • S5 RPC ADMISSION ROOT-CAUSE REPAIR

- Canonical branch: phase-19-e2e-harness.
- Verified engineering HEAD: 3e84ff7e2ce2cb83701729a79c62a3f6dd9a03ca.
- S5 #42 / run 35837830127 is terminal FAILURE with a published artifact. Artifact forensic classification: 164/164 tiles accounted, 0 complete, 164 incomplete, 6,232 retryable evaluations, 0 observations. This is not market-negative evidence.
- Root cause isolated to bounded concurrent RPC admission: 6,002 evaluations reached an exhaustion error with no recorded provider attempt because all temporarily healthy provider slots were occupied by sibling workers.
- Repair 3e84ff7e... adds bounded provider-admission waiting and regression coverage; no provider max-concurrency increase, search-space reduction, or retry-bound expansion was introduced.
- Exact-head Phase-19 #1067 / 35854419968 is terminal SUCCESS with all substantive jobs GREEN.
- Fresh controlled S5 v18 is now admissible from the verified repair HEAD.
- Immediate gate: S5 terminal artifact -> full coverage/evidence forensic -> certification or surgical repair -> only then S0.
- data-plane-ci remains absent and is not GREEN.
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

## LATEST AUTHORITATIVE SYNC • 2026-09-23 • FRESH S5 AFTER RPC REPAIR
- Current branch: `phase-19-e2e-harness`.
- Verified engineering HEAD before this kick: `fe3ecb1c1382fc900fb01ce166aa864b0c02a598`.
- Phase-19 #1073 / 35874255822 is terminal GREEN.
- Next active gate: one fresh S5 read-only run triggered from this exact verified lineage, followed by artifact forensic coverage/economic decision.
- S0 remains blocked until S5 complete declared-domain evidence is certified.
- LIVE SIGNING = BLOCKED; PUBLIC BROADCAST = BLOCKED; LIVE CAPITAL = LOCKED.


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