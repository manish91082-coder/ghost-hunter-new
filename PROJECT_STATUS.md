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
- Current HEAD at this sync: `b19c8c08c3741a51068f6e043521452f1ece8ab4` (`fix(P0): forward scheduler circuit settings from factory`).
- Latest verified engineering commit at this sync: `b19c8c08c3741a51068f6e043521452f1ece8ab4` (`fix(P0): forward scheduler circuit settings from factory`).
- Latest verified Phase-19 CI certification: workflow run `615` / run ID `35350779558` **GREEN** on `59f1e88fd841e2e91a427eaca0329960dd759ac4`; Solidity compilation, EVM integration (**14 tests**), Polygon fork protocol smoke (**3 tests**), Polygon fork execution probe (**1 test**), and the full Phase-19 unittest suite (**717 tests, 0 failures, 0 errors**) all completed successfully. The workflow checked out the exact branch HEAD with `fetch-depth: 0`.
- The latest First-Hunt runs are read-only evidence only. First-Hunt #18 uses the bounded RPC scheduler head `b19c8c08...`; verify its final outcome from Actions before treating it as current market evidence.
- The verified cleanup removes the duplicate Governor test module `tests/phase19/test_execution_governor.py`; canonical Governor coverage remains in `tests/phase19/test_governor.py` and the existing canonical pipeline tests. The canonical Governor implementation remains `phantomx/governor.py`.
- `phantomx/live_opportunity_pipeline.py` provides concrete cross-venue discovery → complete economic evaluation → deterministic execution assembly → EVM preflight. It performs no signing, submission, broadcast, or live-capital operation.
- `phantomx/live_canonical_governor.py` composes concrete discovery, economics, assembly, preflight, and the repository's canonical Governor before the signer boundary. It performs no signing, submission, broadcast, or live-capital operation.
- `phantomx/execution_coordinator.py` is the durable bridge from proven route/economic evidence through nonce reservation/binding, EVM preflight, canonical Governor, signer, and transaction persistence. Failures before signing release an uncommitted nonce reservation; post-signing persistence failures retain the reservation for forensic recovery.
- `phantomx/live_execution_coordinator.py` now bridges concrete cross-venue discovery and complete economic evaluation into `prepare_signed_execution`; it performs no public/private relay submission or live-capital operation.
- Concrete cross-venue discovery remains pinned to one canonical Polygon block across both supported venue directions and the complete supplied loan-size frontier.
- `phantomx/opportunity_economics.py` remains the economic binding layer: discovered candidates are joined to explicit valuation/cost evidence to create hash-bound `EconomicProof`; below-floor proofs remain evidence-only and cannot reach execution.
- `phantomx/loan_optimizer.py` remains exact-domain and complete: all supplied integer amounts are evaluated, mixed block/chain candidates are rejected, and ties resolve to the smaller loan.
- The economic invariant is unchanged: realized net profit must be **strictly greater than $0.20 after all applicable costs**.
- Current First-Hunt loan frontier at this sync is expanded to 17 explicit USDC sizes from $100 through $250,000; the frontier is complete only over these supplied amounts.
- First-Hunt #16 / run ID `35341127352` is **GREEN** on `55614a3d...`; the corrected DYN-2 path reuses exact route observations rather than duplicating RPC calls. First-Hunt #18 is the current scheduler-head verification run; use only its final result for current market evidence.
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
- Current GitHub head includes only operator-workflow/control-plane changes after the latest verified scanner head; the latest applicable market evidence remains First-Hunt #18 on `b19c8c08...` unless a newer exact-head run is explicitly verified.

- DYN-3 implementation is now present at `phantomx/gas_observation.py` with a read-only `eth_estimateGas` boundary at a specified block plus observed EIP-1559 fee inputs. `phantomx/polygon_rpc_http.py` allowlists only the required read methods and still blocks transaction-send methods.

- DYN-3 is now GREEN at the deterministic test level: exact execution-path gas estimation is pinned to a block, EIP-1559 fee inputs are separately observed, and conservative gas USD conversion requires an explicit evidence-backed native/USD valuation input. No loan-percentage gas model exists.
- First-Hunt run `#21` / run ID `35347557050` is on the earlier gas-cost module head `0aef564a...`; it is not treated as current-head market evidence. Current market evidence must be re-established after the control-plane sync when needed.

- DYN-4 is GREEN at deterministic test level: `phantomx/native_valuation.py` derives conservative POL/USD evidence from exact WPOL→USDC quotes at one block; `phantomx/gas_cost.py` converts transaction-level gas bound to USD using that evidence; `phantomx/live_economic_binding.py` binds exact USDC settlement and external costs into `EconomicProof` without double-counting swap fee/price-impact already reflected in exact AMM outputs. Strict net remains `> $0.20`.
