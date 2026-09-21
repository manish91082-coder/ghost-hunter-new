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

## DYNAMIC MARKET AUTONOMY
- Canonical policy: `PHANTOMX_DYNAMIC_MARKET_AUTONOMY_POLICY.md`.
- Integration sequence: DYN-1 live Aave liquidity/premium -> DYN-2 liquidity-aware loan domain -> DYN-3 exact execution gas -> DYN-4 all-cost EconomicProof -> DYN-5 final requote/state lock -> DYN-6 strategy registry -> DYN-7 adaptive RPC fleet -> DYN-8 scheduler -> DYN-9 external gates -> DYN-10 controlled execution/PnL.
- Market-dependent values remain dynamic; only safety invariants and explicit policy bounds are frozen.

## CURRENT STATE
- Branch: `phase-19-e2e-harness`
- Current HEAD at this sync: `810b190e3660394bc3be2923d3dc01f958457e57` (`fix: fail closed on incomplete first-hunt coverage`).
- Latest verified engineering commit at this sync: `810b190e3660394bc3be2923d3dc01f958457e57` (`fix: fail closed on incomplete first-hunt coverage`).
- Latest verified Phase-19 CI certification: workflow run `#871` / run ID `35505502629` **GREEN** on `9b3fd4660f23d730d45076d5d7368ce3180486ba`; Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full Phase-19 unittest suite (**878 tests, 0 failures, 0 errors**) all completed successfully. Workflow run `#872` is the current post-gate verification on HEAD `810b190e3660394bc3be2923d3dc01f958457e57`.
- First-Hunt run `#44` / run ID `35505502646` is the latest completed read-only hunt before the fail-closed coverage gate: **GREEN**, `1,216` observations, `0` gross-positive, `0` post-flash-positive, best gross `-$0.122095`, best post-flash `-$0.172095`, pinned block `94130318`. However, only **32/36 pair/fee tiles** completed, so it is **not universe-exhaustion evidence**. First-Hunt `#45` is the current HEAD `810b190e...` verification run.
- The verified cleanup removes the duplicate Governor test module `tests/phase19/test_execution_governor.py`; canonical Governor coverage remains in `tests/phase19/test_governor.py` and the existing canonical pipeline tests. The canonical Governor implementation remains `phantomx/governor.py`.
- `phantomx/live_opportunity_pipeline.py` provides concrete cross-venue discovery → complete economic evaluation → deterministic execution assembly → EVM preflight. It performs no signing, submission, broadcast, or live-capital operation.
- `phantomx/live_canonical_governor.py` composes concrete discovery, economics, assembly, preflight, and the repository's canonical Governor before the signer boundary. It performs no signing, submission, broadcast, or live-capital operation.
- `phantomx/execution_coordinator.py` is the durable bridge from proven route/economic evidence through nonce reservation/binding, EVM preflight, canonical Governor, signer, and transaction persistence. Failures before signing release an uncommitted nonce reservation; post-signing persistence failures retain the reservation for forensic recovery.
- `phantomx/live_execution_coordinator.py` now bridges concrete cross-venue discovery and complete economic evaluation into `prepare_signed_execution`; it performs no public/private relay submission or live-capital operation.
- Concrete cross-venue discovery remains pinned to one canonical Polygon block across both supported venue directions and the complete supplied loan-size frontier.
- `phantomx/opportunity_economics.py` remains the economic binding layer: discovered candidates are joined to explicit valuation/cost evidence to create hash-bound `EconomicProof`; below-floor proofs remain evidence-only and cannot reach execution.
- `phantomx/loan_optimizer.py` remains exact-domain and complete: all supplied integer amounts are evaluated, mixed block/chain candidates are rejected, and ties resolve to the smaller loan.
- The economic invariant is unchanged: realized net profit must be **strictly greater than $0.20 after all applicable costs**.
- Current First-Hunt loan frontier uses the 17 seed USDC sizes plus a live dynamic extension. The latest completed hunt reached **19 sizes**, ending at live Aave-derived ceiling `539762` USDC.
- Historical First-Hunt evidence remains read-only. #44 on `9b3fd466...` is the last completed scan, but its 4 unresolved tiles prevent treating it as complete. #45 on `810b190e...` is the active current-head recheck with fail-closed coverage semantics.
- Frozen external evidence artifact remains `e117b6550686cf5e0ff787d9bd7d85e83996db07`; engineering commits after that artifact do not retroactively alter its identity. The latest verified engineering commit is **112 commits ahead** of the frozen artifact with no commits behind it, based on GitHub commit comparison. The current HEAD adds only status documentation on top of that verified engineering commit.
- Consolidated external-evidence validation remains hard-bound to the frozen external artifact and requires independent lane evidence for signer, Polygon authority, private relay, shadow/staging, and realized PnL.
- Operator preflight still requires current HEAD to descend from the frozen artifact and rejects missing or contradictory evidence.
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

## DYNAMIC MARKET / AUTOMATION POLICY

The canonical dynamic-market requirements are frozen in `PHANTOMX_DYNAMIC_MARKET_AND_AUTOMATION_POLICY.md`. Market-derived values must remain runtime-dynamic. Gas must be modeled as transaction-level gas usage and effective gas price, never as a percentage of loan principal. Loan sizing must be bounded by live Aave reserve liquidity plus live venue liquidity/price-impact and repayment constraints. The RPC layer must use a large replaceable registry with bounded active-provider selection, rate limiting, circuit breakers, caching and block-pinned reads; it must not bombard hundreds of providers per task. New strategy classes require controlled adapter, economic and adversarial verification before production activation.

- DYN-1 is integrated by `scripts/first_hunt_live_scan.py`: live Aave reserve liquidity and `FLASHLOAN_PREMIUM_TOTAL` are read at the same pinned block; the loan domain is bounded by Aave liquidity with 5% fixed safety headroom, and each observation records both post-swap gross delta and post-flash-premium delta. Gas remains transaction-level and separate.
- DYN-2 is now being integrated through `phantomx/dynamic_route_guard.py`: the candidate size is bounded by exact two-direction route executability and a fixed 100 bps maximum route-rate degradation policy relative to the smallest successful probe. This is exact over the supplied discrete domain only; no continuous-optimum claim is made.


## SPEED / STRATEGY EXPANSION CONTROL

- `phantomx/rpc_scheduler.py` now defines a bounded provider-fleet scheduler. A large registry may hold hundreds of non-secret provider records, but each task is assigned only to a small active subset with per-provider concurrency limits and circuit-breaker behavior.
- `phantomx/strategy_registry.py` now tracks one canonical strategy plus discovery-only expansion candidates. Discovery registration never authorizes production execution.
- Research confirms Polygon has current Uniswap V4 and Ramses V3 deployments; those are registered as discovery-only until exact adapters and evidence gates exist.


## CROSS-AI CONTINUITY
- Canonical durable continuity manifest: `PHANTOMX_PROJECT_RESUME_MANIFEST.md`.
- Any future AI/operator must read the resume manifest, then this status file, then latest relevant Actions before writing.
- Chat memory is supportive only; Git is the durable project memory.

- One-click operator interface is now present at `.github/workflows/phantomx-one-click.yml` with AUDIT, TEST, LIVE-HUNT, PREPARE-STAGING, STAGING, PRODUCTION-READY-CHECK and LIVE-EXECUTION modes. The LIVE-EXECUTION path is intentionally fail-closed until external evidence is accepted.
- Current HEAD `810b190e...` contains the fail-closed First-Hunt coverage gate and post-flash triage metrics. Latest exact-head market evidence is First-Hunt #45, pending final conclusion at this sync.

- DYN-3 implementation is now present at `phantomx/gas_observation.py` with a read-only `eth_estimateGas` boundary at a specified block plus observed EIP-1559 fee inputs. `phantomx/polygon_rpc_http.py` allowlists only the required read methods and still blocks transaction-send methods.

- DYN-3 is now GREEN at the deterministic test level: exact execution-path gas estimation is pinned to a block, EIP-1559 fee inputs are separately observed, and conservative gas USD conversion requires an explicit evidence-backed native/USD valuation input. No loan-percentage gas model exists.
- First-Hunt run `#21` / run ID `35347557050` is on the earlier gas-cost module head `0aef564a...`; it is not treated as current-head market evidence. Current market evidence must be re-established after the control-plane sync when needed.

- DYN-4 is GREEN at deterministic test level: `phantomx/native_valuation.py` derives conservative POL/USD evidence from exact WPOL→USDC quotes at one block; `phantomx/gas_cost.py` converts transaction-level gas bound to USD using that evidence; `phantomx/live_economic_binding.py` binds exact USDC settlement and external costs into `EconomicProof` without double-counting swap fee/price-impact already reflected in exact AMM outputs. Strict net remains `> $0.20`.

- DYN-5 deterministic gate is GREEN: Phase-19 run #617 / ID `35356389228` passed on current DYN-5 head. `phantomx/final_state_lock.py` requires the final route, valuation evidence, gas evidence and EconomicProof to share the exact current block, and rejects stale, mismatched or below-floor final state.

- S1 automation lane is now explicit at `.github/workflows/s1-qsv3-live-read.yml`: push-triggered on S1 code changes plus manual dispatch, bounded/cancel-in-progress, read-only, and artifact-backed. S1 remains discovery-only until economic/adversarial/authority gates pass.

- S1 QuickSwap V3 live-hunt automation is now isolated at `.github/workflows/s1-qsv3-live-read.yml` with manual dispatch, push-triggering for S1/common route code, artifact publication, and shared market-hunt concurrency to prevent cross-strategy RPC overlap. First successful S1 automated run has not yet been completed on the current `617e203...` trigger-cleanup head.
- S0 optimized First-Hunt run #29 / ID `35364241078` is GREEN on `b6f291f6...`: 920 observations on DRPC and 960 on PublicNode, zero gross-positive, best gross `-$0.166871` and `-$0.262327` respectively; live Aave USDC dynamic ceiling was `580980.874662` USDC. 1RPC failed route completeness and is not counted as successful observation evidence.


## CURRENT VERIFIED SYNC • 2026-09-20

- Canonical HEAD: `810b190e3660394bc3be2923d3dc01f958457e57`.
- Phase-19 run `#871` on `9b3fd466...`: GREEN, **878 tests**. Post-gate run `#872` is running on the current HEAD.
- First-Hunt #44 on `9b3fd466...`: **1,216 observations**, no gross-positive and no post-flash-positive observation; best gross `-$0.122095`; best post-flash `-$0.172095`; block `94130318`.
- First-Hunt #44 had **4/36 unresolved pair/fee tiles**. Therefore it is market evidence only, not complete search/exhaustion evidence.
- First-Hunt #45 on `810b190e...` is the first hunt after the fail-closed coverage correction. A non-COMPLETE tile now causes a non-zero exit while the artifact is still preserved.
- Historical Polygon Universe Crawler #5 on `751024247...` completed GREEN for blocks `0-99999` against fixed snapshot `94129645`, across six declared venues. Its automatic continuation was disabled in that run, so the campaign has **not** reached historical exhaustion.
- P0 remains blocked on a genuine currently executable opportunity, complete market coverage where claimed, external signer/provider/relay evidence, shadow/staging, controlled execution, and independent realized PnL > $0.20.


## CURRENT VERIFIED SYNC • 2026-09-20 16:46 IST

- Canonical branch HEAD: `7527ff10b2143aafe02cae4d55a0fb7f0f83d503` (`fix: propagate route failure evidence`).
- Phase-19 run #885 on prior HEAD `79bda3c...`: GREEN. Current HEAD run #886 is the active deterministic verification.
- First-Hunt #45 on `810b190e...` was correctly FAILED because coverage was only 32/36 tiles. Its best gross was `-$0.122175` and post-flash best was `-$0.172175` at block `94131367`.
- First-Hunt #49 on `bdde95c...` was superseded/cancelled by a newer code change before completion; it is not market evidence.
- Current First-Hunt #50 targets `7527ff10...`; current inventory #19 also targets the same HEAD.
- The opportunity-discovery layer now retains per-loan-size failure evidence and classifies explicit RPC/infrastructure failures as retryable. Cross-venue discovery now propagates forward/reverse failure evidence instead of discarding it.
- Historical Polygon Universe Crawler remains non-exhausted. The last certified historical slice reached only `0-99999` against a fixed snapshot and required explicit continuation.
- Production execution remains BLOCKED; public broadcast is BLOCKED; live capital remains LOCKED. No profitability certificate has been accepted.

## CURRENT AUTHORITATIVE SYNC • 2026-09-20 • LATEST

- Canonical HEAD: `bd991f7d4c35e84db50947f1a235f16bc7eb37cc` (`fix: hard-lock canonical history snapshot and resume`).
- Latest completed Phase-19: run `#899` / `35513275509` GREEN on `dccae7dc...`; run `#900` is the active verification on the current HEAD.
- Canonical historical campaign: `polygon-genesis-94135487`, fixed snapshot `94135487`, immutable campaign commit `68b35b09441d9d7f3b64530096114fb66eb78938`.
- Canonical bootstrap evidence from run `#12` certifies slice `0-99999` with `next_from_block=100000`. Historical exhaustion is not achieved.
- Runs created from older cursor races (`polygon-genesis-94135367`, `polygon-genesis-94136591`) are non-canonical. New resolver logic rejects them.
- History crawler now uses a single-flight concurrency lock and a dedicated `.github/PHANTOMX_HISTORY_KICK` trigger. Ordinary code changes no longer bootstrap a new history campaign.
- Current broad S0 hunt #52 was cancelled before completion. No current-head S0 profitability certificate exists. Latest completed broad evidence remains #45 on `810b190e...`: 1,216 observations, 0 gross-positive, 0 post-flash-positive, with 32/36 tiles complete.
- S10 QSV3↔Ramses V3 produced gross-positive observations on an applicable older scanner head, but best post-flash result remained negative (`-$0.118598`), so no economic certificate exists.
- S1 and S9 latest completed reads remain non-profitable on their applicable scanner heads. Production execution, signing, public broadcast and live capital remain blocked/locked.

## CURRENT AUTHORITATIVE SYNC • 2026-09-20 • POST-RESUME KICK

- Current HEAD: `af4f6dc4ef007c503cef01c078e92e98a931ec3a` (`chore: trigger canonical history resume`).
- Phase-19 run `#902` / `35513839907` is GREEN on this HEAD.
- Historical Universe Crawler run `#27` / `35513839962` is active on this HEAD and has resolved the canonical campaign exactly as `polygon-genesis-94135487`, snapshot `94135487`, resume range `100000-199999`.
- Six venue inventory jobs are currently running for that exact slice; no claim of completion is made until all six plus slice certification pass.
- This confirms the history campaign is no longer starting from an accidental live-head snapshot. Legacy rogue campaign runs remain rejected/non-canonical.


## CURRENT AUTHORITATIVE SYNC • 2026-09-20 • HEAD 00547

- Canonical HEAD: `00547b3c22d49dd21b0cb5c48c0c2b7b99b84cfb`.
- Phase-19 run #905 / `35514485134`: GREEN on this HEAD.
- Canonical historical campaign: `polygon-genesis-94135487`, fixed snapshot `94135487`. Certified contiguous slices now cover `0-99999` and `100000-199999`; next canonical slice is `200000-299999`.
- Historical crawler run #27 / `35513839962`: GREEN, certified slice `100000-199999`, next cursor `200000`. Run #29 is the active canonical continuation at `200000-299999`.
- Legacy crawler run #28 failed because it carried an older workflow commit into the locked campaign. New campaign logic rejects that mismatch; no market inventory result from #28 is accepted.
- S0 First-Hunt #53 / `35514040865` is the latest clean current scanner run on `625f6385...`; it is still in progress. It includes per-size failure retention and one bounded retry for retryable RPC/infrastructure failures.
- Latest completed broad S0 hunt before #53 remains #45: 1,216 observations, 0 gross-positive, 0 post-flash-positive, with incomplete 32/36 tile coverage. It is not exhaustion proof.
- Latest completed S10 QSV3↔Ramses V3 run #13 on `2db8206...`: 38 observations, 3 gross-positive, best gross `+$0.006402`, but best post-flash `-$0.118598`. No EconomicProof certificate.
- Latest completed S9 QSV2↔Ramses V3 run #14 on `d480ae7...`: 38 observations, 0 gross-positive, best gross approximately `-$0.164295`.
- Live signing remains BLOCKED; public broadcast BLOCKED; live capital LOCKED. Realized net profit > $0.20 is NOT proven.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • POST-FIRST-HUNT-V4-RPC-FIX

- Canonical branch: `phase-19-e2e-harness`.
- Latest code/evidence lineage entering this status checkpoint: `62622c169258d0d506402777b4d959fc75a98a44` (cycle-record documentation commit). This status update is itself the canonical documentation checkpoint on top of that lineage.
- First-Hunt #66 is CLOSED as **INCOMPLETE**, not a market-negative certificate: 33/36 valid shards, 33/36 tiles, 1,280 observations, 0 gross-positive, 0 post-flash-positive; best gross `-$0.153253`, best post-flash `-$0.203253`.
- Root cause from #66: contract-level `execution reverted` responses were incorrectly treated as retryable by the RPC failover layer, causing semantic route failures to rotate through the provider fleet and contributing to timeout/incomplete cells.
- Correction recorded in `PHANTOMX_FIRST_HUNT_V4_RPC_FORENSIC.md`: semantic EVM execution reverts are now non-retryable; transport, rate-limit, timeout, gateway and historical-state failures remain retryable.
- `tests/phase19/test_rpc_failover.py` now explicitly verifies that semantic reverts are not blindly retried across providers.
- `scripts/aggregate_first_hunt_shards.py` now reports the correct 36-shard denominator.
- Phase-19 verification runs `#939`, `#940`, `#941`, and `#942` are GREEN on the post-fix lineage.
- First-Hunt #67 is the clean rerun launched from the verified post-fix HEAD. Shared Polygon block resolution succeeded. Latest observed run state during this cycle: 37 jobs total, 35 completed, 31 successful, 4 failed, 1 running, 1 queued; final aggregate was not yet available at the last observation.
- Historical Polygon Universe Crawler remains active under `polygon-genesis-94135487`; continuation run `#84` had 5/6 venue inventory jobs completed and Ramses V3 still running at the last observation. Historical exhaustion is not achieved.
- No gross-positive or post-flash-positive observation is promoted to EconomicProof automatically. Exact gas, complete costs, final requote/state lock, EVM preflight, external signer/provider/private-relay evidence, staging, controlled execution and realized-PnL proof remain separate gates.
- **LIVE SIGNING = BLOCKED. PUBLIC BROADCAST = BLOCKED. LIVE CAPITAL = LOCKED.**
- **Process rule:** every substantive execution cycle must create/update the relevant evidence/status file before the cycle is reported complete.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • SEMANTIC-REVERT COVERAGE REPAIR

- First-Hunt #67 / run ID `35536094045` is now closed with **30 jobs total: 26 successful, 4 failed**. The four failed atomic cells were fee 100/pair 4, fee 100/pair 6, fee 100/pair 1, and fee 500/pair 5. No complete 36-cell market certificate is accepted from this run.
- The failure pattern exposed a second-layer classifier bug after the earlier RPC-layer repair: `phantomx/rpc_failover.py` treated `execution reverted` as terminal, but `phantomx/opportunity_discovery.py` still promoted any `RPCPoolError` to retryable status before reading the semantic message.
- Engineering repair commit: `014e14ed25859a80d0f057c3e6de76adac1d4cb3` checks for semantic `execution reverted` first and returns terminal classification while preserving genuine transport/rate-limit retry behavior.
- Regression commit: `864f45b9418cf019bd4f6ab1acda4bb2bd565f21` adds explicit semantic-revert and 429 transport classification tests.
- Cycle evidence: `PHANTOMX_CYCLE_2026-09-21_SEMANTIC_REVERT_COVERAGE_FIX.md` records the forensic finding, repair, and current verification limitation.
- First-Hunt #67 produced 37 published artifacts, including the read-only live-scan artifact, but no aggregate market-complete certificate was produced. The run is therefore treated as incomplete evidence, not as a market-negative result.
- GitHub combined commit-status queries for the new repair commits currently expose no published status checks, so **CI GREEN is not claimed yet** for the new repair lineage.
- The next admissible market step is: verify Phase-19 CI on the repair lineage, then launch a fresh isolated 36-cell First-Hunt. The fresh run must prove every atomic shard and every pair/fee tile complete before any exhaustion conclusion.
- Profitability remains unproven. Exact execution-path gas, complete-cost EconomicProof, final requote/state lock, external signer/provider/private-relay evidence, staging, controlled execution and realized PnL > $0.20 remain separate gates.
- **LIVE SIGNING = BLOCKED. PUBLIC BROADCAST = BLOCKED. LIVE CAPITAL = LOCKED.**

**Process gate reaffirmed:** substantive cycle = work → evidence/step file → `PROJECT_STATUS.md` update → verification state → report.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • SURGICAL REPOSITORY CLEANUP

- Repository structure audit recorded in `PHANTOMX_REPOSITORY_STRUCTURE_AUDIT_2026-09-21.md`.
- Canonical branch inventory before cleanup: **320 files** across the canonical `.github / contracts / phantomx / scripts / tests` structure; post-cleanup recount is **318 files**. The canonical branch contains the expected architecture; legacy `v2 / v3 / common / agents` runtime trees are absent.
- Scope/drift review against `PROJECT_DETAILS.md`, `PHANTOMX_PROJECT_RESUME_MANIFEST.md`, `PHANTOMX_POLYGON_ARBITRAGE_STRATEGY_CATALOG.md`, and `PHANTOMX_DYNAMIC_MARKET_AUTONOMY_POLICY.md` found no unambiguous architectural drift in the canonical tree. Historical continuity sections are retained as historical evidence and do not override the latest status section.
- Surgical deletion #1: `scripts/README.tmp` removed because its complete content was only `temporary`.
- Surgical deletion #2: `tests/phase19/test_control_room_validator.tmp` removed because it was an obsolete `.tmp` pointer to the canonical `test_control_room_validator.py` suite.
- Related control-room governance notes and changelog files were intentionally **preserved** because they have an identifiable audit/coordination role.
- No core `phantomx/` runtime module, contract, workflow, certification test, strategy adapter, policy, evidence record, or continuity manifest was deleted in this cleanup.
- Cleanup deletion commit: `7b352e5c870f6560afe4011c94e8984da9fc5a5a`. The status checkpoint is the documentation commit immediately following the cleanup.
- Inventory correction: an intermediate execution note reported 284 files; an independent directory-by-directory recount established 320 before cleanup and 318 after cleanup. The corrected figures are the authoritative audit values.
- CI GREEN is not claimed for the post-cleanup lineage until GitHub Actions publishes successful verification.
- Production state remains unchanged: profitability not proven; external signer/provider/private-relay/shadow evidence not accepted; live signing blocked; public broadcast blocked; live capital locked.

**Process gate reaffirmed:** inventory → dependency/reference judgment → evidence file → surgical mutation → `PROJECT_STATUS.md` update → post-mutation verification → report.

## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • REPOSITORY STRUCTURE / NO-DRIFT AUDIT

- Canonical repository and branch were re-verified: `manish91082-coder/ghost-hunter-new` / `phase-19-e2e-harness`.
- Architecture drift audit against the resume manifest, `PROJECT_DETAILS.md`, strategy catalog and Polygon-wide hunt plan found **no mission-level drift**. The canonical tree still points to the same evidence-first Polygon/Aave V3/QuickSwap V2/Uniswap V3 MVP spine, with discovery-only expansion lanes separated from production authorization.
- A documentation drift was found in `PHANTOMX_PROJECT_RESUME_MANIFEST.md`: it lagged the 2026-09-21 semantic-revert repair. It has now been resynchronized in commit `3cfc43ee2980e3c8f8cd0ddaa3b0b815223d404e`.
- Canonical branch inventory contains **282 tracked files**. Top-level project directories are `.github/`, `contracts/`, `phantomx/`, `scripts/`, and `tests/`.
- Legacy `v2/`, `v3/`, `agents/`, `common/`, notebook, training and historical runner material observed on the separate `master` baseline is absent from the canonical branch. `master` was deliberately left untouched because it is the declared base branch.
- All canonical `phantomx/` modules are part of discovery, economics, execution-integrity, recovery, authority, settlement, strategy or evidence surfaces. `contracts/` and `tests/` map to the EVM/Phase-19 verification boundary. Workflows and scripts map to certification, current/historical discovery, registered strategy reads, evidence validators or operator safety.
- Seven small control-room helper documents look repetitive, but their contents are directly tied to Phase-19 coordination/safety validation. Under the requested rule of deleting only **unrelated** files, they were retained. No unrelated file was proven.
- **Deletion result: 0 files deleted.** This is deliberate surgical behavior, not a skipped cleanup.
- Cleanup evidence file: `PHANTOMX_REPOSITORY_CLEANUP_AUDIT_2026-09-21.md`, committed as `90ab6f05ba8a0a4ffc5120e32cccd9ec7f235431`.
- Current safety and mission gates remain unchanged: **LIVE SIGNING = BLOCKED. PUBLIC BROADCAST = BLOCKED. LIVE CAPITAL = LOCKED.**
- CI for the semantic-revert repair lineage is still not claimed GREEN until an actual applicable workflow run is observed. Fresh First-Hunt must wait for that verification.
