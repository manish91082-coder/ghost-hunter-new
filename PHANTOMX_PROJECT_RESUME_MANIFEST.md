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
