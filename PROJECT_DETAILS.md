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
