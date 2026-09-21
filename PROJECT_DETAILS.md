# PhantomX Flash Loan Ghost Hunter • MVP Project Details

## Mission

Build a Polygon Mainnet flash-loan arbitrage execution system whose MVP is an evidence-driven, fail-closed two-leg `A → B → A` execution pipeline. Live execution and capital remain locked until every production gate is independently proven.

## Canonical MVP Scope

- **Chain:** Polygon Mainnet, chain ID `137`.
- **Flash liquidity:** Aave V3.
- **DEX venues:** QuickSwap V2 and Uniswap V3.
- **Initial assets:** USDC, WETH, WMATIC/POL, WBTC.
- **Route shape:** direct two-leg cross-venue arbitrage.
- **Economic invariant:** realized net profit must be strictly `> $0.20` after all applicable fees, gas, relay cost, price impact, and other modeled costs.
- **Execution safety:** deterministic validation first; AI may rank candidates but cannot override economics, preflight, governance, authorization, nonce, signer, relay, or settlement controls.
- **Private execution:** no public-broadcast fallback.

## Canonical Execution Spine

`LIVE BLOCK → RPC/CHAIN QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT ECONOMICS → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT RECONCILIATION → REALIZED NET PNL`

## Repository Architecture

### `phantomx/`

The production-oriented Phase-19 execution-integrity core. It contains the canonical economics, hashing, execution intent/envelope, authorization, route simulation, quote boundaries, EVM preflight, executor authority, Governor, signer, nonce binding, durable SQLite execution store, replacement/recovery/submission coordination, receipt/reconciliation logic, and related deterministic policy modules.

### `contracts/`

Solidity executor plus isolated test mocks used by the Phase-19 EVM integration harness.

### `tests/phase19/`

Adversarial and integration tests covering economics, hashing, authorization, route/intent mutation, nonce allocation, durable persistence, recovery, replacement chains, signing, submission, executor authority, and coordinator artifact integrity.

### `tests/evm/`

Foundry-based Solidity/EVM integration and Polygon fork probes.

### `.github/workflows/phase19-tests.yml`

Authoritative CI workflow. It installs `requirements-phase19.txt`, compiles the Solidity contract, executes the EVM harness, runs Polygon fork smoke/execution probes, and runs the Python Phase-19 suite.

### `requirements-phase19.txt`

Minimal cryptographic/signing/serialization dependencies required by the Phase-19 core.

### `PROJECT_STATUS.md`

Canonical mission-control and continuity state. It records verified evidence, blockers, current-head state, safety gates, and the next atomic action.

### `PHASE19_*.md`

Phase-specific evidence and checkpoint records. They are retained as audit/continuity evidence. Historical statements inside them must not override the canonical current state in `PROJECT_STATUS.md`.

## Integration Contract

The MVP is considered internally integrated only when every artifact crosses the following controlled boundaries without mutation or ambiguity:

`QuoteSnapshot → RouteSimulation → EconomicProof → ExecutionIntent → Calldata/Route Commitment → Authorization → EVMPreflight → GovernorDecision → Nonce Binding → Signed Transaction → Durable TransactionRecord → Private Submission → Receipt Observation → Reconciliation → Realized PnL`

The coordinator is the narrow assembly path that connects these boundaries. Any mismatch causes fail-closed rejection.

## Evidence Policy

- Implementation is not proof.
- Unit-test success is not fork proof.
- Fork proof is not production proof.
- Historical data is not current authority evidence.
- Missing or contradictory evidence is `UNKNOWN/BLOCKED`.
- No live signing, public broadcast, private-key exposure, or live-capital authorization occurs during Phase-19 certification.

## Production Inputs Still External

Production readiness requires controlled external confirmation of:

1. approved Polygon RPC provider set and quorum policy;
2. intended deployed executor address and matching runtime bytecode/owner/domain evidence;
3. expected production signer address, without exposing private key material;
4. approved private relay capability with no public fallback;
5. production-like shadow/staging and final settlement evidence.

Until these are proven, **LIVE CAPITAL = LOCKED**.

## Repository Cleanliness Rule

No legacy v2/v3 runtime, obsolete configuration, generated trading logs, credentials, historical live runners, notebooks, or unrelated AI/training artifacts belong in the MVP execution tree. New files must have a direct and documented role in the canonical MVP spine or its certification evidence.

## Current Safety State

**Phase:** 19 execution-integrity / E2E certification  
**Production readiness:** NOT ACHIEVED  
**Live mainnet execution:** BLOCKED  
**Live capital:** LOCKED

## Current continuity / evidence synchronization • 2026-09-21

- Durable project-memory files are `PROJECT_MEMORY.md` and `PHANTOMX_PROJECT_RESUME_MANIFEST.md`; `PROJECT_STATUS.md` is the canonical live mission-control state.
- `PROJECT_DETAILS.md` defines architecture, scope and integration contracts. It is synchronized whenever those architectural/operating facts materially change; it is not rewritten blindly for every chat message.
- Current branch HEAD before this update: `063090201ebe9ba3c17589b34d9b0f9e0ffe5d69`.
- First-Hunt #68 / run `35566476146` is complete for its declared domain: 36/36 atomic cells covered, 1,246 route observations, 0 gross-positive and 0 post-flash-positive observations at Polygon block 94,176,798.
- Four tiles are terminal `COMPLETE_NO_COMMON_ROUTE`; this is complete coverage of those cells, not universe-wide exhaustion.
- Hunt artifact records `economic_certification=NOT_PERFORMED` and `profit_claim=NONE`.
- The next engineering gate is therefore not a new random discovery expansion: reconcile complete S0 coverage with the existing exact-gas / live-valuation / EconomicProof boundary and determine whether a genuine candidate exists for downstream execution-integrity certification.
- Production remains blocked: no signer activation, broadcast, live capital, or realized-PnL authorization has been enabled.

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


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 COVERAGE CONTRACT REPAIR

- The S3 read-only discovery lane now has an explicit coverage contract: deterministic absence of a required venue pool is terminal `COMPLETE_NO_COMMON_ROUTE`; RPC/semantic/unknown failures remain `PARTIAL_INCOMPLETE`; only full declared tile coverage yields aggregate `COMPLETE`.
- S3 aggregate completion is now bound to the exact declared matrix of **6 Ramses V3 tick spacings × 4 Uniswap V3 fee tiers × active live pair count**, with observed-tile count also required to equal the expected count.
- Incomplete coverage causes a non-zero scanner exit even when the RPC pool returns a top-level result. This preserves evidence while preventing false workflow-success from becoming market-success.
- This is an operating-contract correction only; no signing, submission, broadcast, or live-capital capability was added.
- Exact-head Phase-19 #982 / `35580051618` is GREEN with 899 tests.
- S3 repair verification #18 / `35579964402` remains in progress; production remains blocked until all downstream evidence gates are independently proven.


## CURRENT AUTHORITATIVE SYNC • 2026-09-21 • S3 RPC FAILOVER BOUNDARY REFINEMENT

- S3 evidence preservation is now unconditional: artifact upload executes even when the read-only scanner exits non-zero for incomplete coverage.
- The RPC failover policy now distinguishes **reasoned execution reverts** (terminal semantic evidence) from **uninformative `execution reverted: Unexpected error`** responses (recoverable provider anomaly). The latter is retried only through the existing bounded fleet/recovery mechanism.
- This preserves the invariant that provider-specific read anomalies must not silently delete a logical route task, while still failing closed when independent providers cannot return a usable answer.
