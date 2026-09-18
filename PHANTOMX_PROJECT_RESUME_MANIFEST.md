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
