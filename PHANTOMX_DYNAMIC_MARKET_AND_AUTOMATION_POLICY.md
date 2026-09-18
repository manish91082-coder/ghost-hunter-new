# PHANTOMX Dynamic Market, Liquidity, Gas & RPC Automation Policy

## Purpose

This document is the canonical design rule for turning PHANTOMX from a fixed-grid research scanner into a goal-driven automatic Polygon arbitrage MVP.

The governing principle is:

> **Market truth is dynamic. Safety policy is fixed.**

Market-dependent values must be discovered and bound at runtime from fresh, evidence-backed on-chain observations. Deterministic safety, authorization, proof, and execution rules remain immutable policy gates.

## 1. Canonical mission

Target:
`LIVE MARKET -> EXACT ROUTE -> COMPLETE COSTS -> STRICT NET > $0.20 -> PREFLIGHT -> GOVERNOR -> CONTROLLED SIGNER -> PRIVATE SUBMIT -> RECEIPT -> INDEPENDENT REALIZED PNL > $0.20`

No live signing, public broadcast, or live capital is allowed merely because a scanner finds a positive gross spread.

## 2. Current canonical execution scope

- Chain: Polygon PoS Mainnet, chain ID 137.
- Flash liquidity: Aave V3.
- Current canonical venues: QuickSwap V2 and Uniswap V3.
- Initial production asset scope: USDC, WETH, WPOL/POL, WBTC.
- Current First-Hunt exploratory assets may be broader, but exploratory assets do not automatically become production scope.
- Current route family: direct two-leg A -> B -> A.
- Current Uniswap V3 fee search: 100, 500, 3000, 10000 fee units where the pool exists.
- Execution remains fail-closed.

## 3. Dynamic-by-default variables

The following must not become permanent market constants:

- current block number and block hash
- RPC provider selected for each read
- token/pool availability
- token decimals and metadata when not already cryptographically/contract-bound
- QuickSwap V2 reserves
- Uniswap V3 pool address, active liquidity, sqrtPriceX96, current tick, initialized ticks needed for bounded impact analysis
- Uniswap V3 fee tier availability
- Aave flashloan premium
- Aave reserve liquidity available for the requested asset
- executable loan maximum after repayment premium
- route-specific price impact
- exact quote outputs
- gas estimate / gasUsed for the exact execution path
- base fee, priority fee, max fee and authorized gas ceiling
- native-token USD valuation
- private relay fee / inclusion cost when applicable
- nonce and transaction freshness
- deadline / block freshness
- competitive/MEV risk bounds
- any market-derived ranking score

These values must be observed again at the final requote/state-lock boundary.

## 4. Gas is NOT a percentage of loan size

This is a non-negotiable economic rule.

Gas is a transaction-level resource. Do NOT model gas as `loan_amount * gas_percent`.

For an EIP-1559-style transaction, the economic gas cost is driven by the gas actually consumed and the effective gas price:

`gas_cost_native = gas_used * effective_gas_price`

and then:

`gas_cost_usd = gas_cost_native * live_native_token_usd`

The exact execution path determines gas usage. Loan size can influence route calldata or swap execution behavior indirectly, but gas must never be assumed to be a fixed percentage of the borrowed principal.

Therefore a hypothetical "1% gas" input is rejected as an invalid market model. A large loan does not automatically imply proportionally larger gas.

Before execution, the system must bind a conservative gas ceiling using route-specific EVM estimation/preflight. After execution, receipt `gasUsed` and effective gas price are used for realized reconciliation.

## 5. Flash-loan fee is dynamic

Do not hardcode an Aave flash-loan percentage such as 0.09%.

Aave V3 exposes `FLASHLOAN_PREMIUM_TOTAL`; the current market value must be read from the actual Polygon Aave Pool at the pinned/finalized observation point and included exactly once in the cost breakdown.

The repayment requirement is:

`repayment = principal + live_flashloan_premium`

An authorized zero-fee flash borrower, if ever used, must be proven by the actual Aave authorization path. It must never be assumed.

## 6. Dynamic maximum loan sizing

A fixed loan grid is a temporary discovery aid only. The production optimizer must derive the executable domain dynamically.

For each candidate route:

`dynamic_max_loan = min(
  aave_available_liquidity_bound,
  venue_executable_liquidity_bound,
  route_price_impact_bound,
  executor/risk bound,
  repayment-safe bound
)`

The system must also verify:

1. Aave reserve supports flashloaning the asset.
2. Current available liquidity is sufficient for principal plus required repayment premium.
3. QuickSwap V2 reserve state can support the route without violating configured impact limits.
4. Uniswap V3 active liquidity/tick path can support the swap; quotes that cross unavailable liquidity or revert are rejected.
5. Exact quotes are evaluated at one pinned block.
6. If the route cannot be proven executable at a size, that size is not part of the optimization domain.
7. No fixed `$250k` or other static ceiling may override a lower live liquidity bound.
8. The optimizer may search above a historical grid only when the live hard bounds prove the domain.

### Preferred sizing algorithm

Use adaptive, exact evaluation:

1. Discover a live hard upper bound.
2. Establish a conservative lower bound.
3. Evaluate a coarse geometric/discrete set.
4. Identify the best exact region.
5. Densify only around the best region.
6. Requote the final chosen size.
7. Build EconomicProof.
8. Execute only if the strict net-profit gate passes.

The optimizer must never turn a liquidity proxy or ML prediction into execution truth.

## 7. Price impact is part of the size decision

Loan size is not chosen from Aave liquidity alone.

The same loan may be borrowable but economically invalid because the swap moves the AMM price too far.

Therefore the sizing decision is:

`borrowable AND executable AND economically positive`

not merely:

`borrowable`

For Uniswap V3, active liquidity and tick traversal must be considered. For QuickSwap V2, reserve state and exact constant-product quote behavior are authoritative.

## 8. RPC fleet architecture

A large provider registry is useful; querying hundreds of providers for every task is not.

Maintain:

### Provider registry
Potentially 200-500+ provider records over time, containing only non-secret metadata:

- provider ID
- endpoint class
- chain support
- transport capability
- authenticated/public classification
- observed latency
- recent error rate
- rate-limit/quota metadata when documented
- archive support
- websocket support
- health score
- last successful block
- circuit-breaker state

### Active execution/read pool
Use a small dynamically selected subset at runtime.

Selection rules:

- health score
- freshness
- rate-limit headroom
- latency
- chain/feature capability
- historical error rate
- quorum diversity

### No RPC bombing

Never fan out every request to 200-500 endpoints.

Instead:

- cache block identity
- pin all route reads to a selected block
- chunk work into bounded tasks
- use per-provider token buckets
- use circuit breakers
- use exponential backoff
- rotate providers when a quota/error threshold is reached
- retry only idempotent read operations
- avoid duplicate identical reads
- use independent providers for quorum/attestation, not indiscriminate duplication

If one provider fails, another healthy provider may take the task. If quorum evidence is required, the block identity remains explicitly pinned so providers cannot silently contribute observations from incompatible market states.

Polygon documentation explicitly notes that public RPC endpoints can have request limitations and recommends using its maintained provider list; Polygon's own public-operated endpoints were deprecated in 2026, reinforcing that the provider layer must remain replaceable rather than hardcoded.

## 9. Strategy expansion policy

Current canonical strategy is direct two-leg cross-venue arbitrage:

- QuickSwap V2 -> Uniswap V3
- Uniswap V3 -> QuickSwap V2

Future strategy classes may be activated only through a controlled expansion gate:

### Strategy S1
Additional fee-tier / pool discovery within current venues.

### Strategy S2
Additional Polygon DEX venue adapters.

### Strategy S3
Multi-hop / triangular routes.

### Strategy S4
Alternative flash-liquidity sources.

### Strategy S5
Broader token graph / stablecoin routing.

A new strategy is not considered production-ready when its code exists. It requires:

`adapter provenance -> exact quote tests -> route invariants -> economic proof -> adversarial tests -> fork evidence -> production authority review`

AI may rank strategy candidates. It cannot override deterministic safety/economic gates.

## 10. Automatic MVP control loop

The target automatic loop is:

`DISCOVER -> PIN BLOCK -> QUORUM/HEALTH -> DISCOVER POOLS -> EXACT QUOTES -> DYNAMIC MAX LOAN -> ADAPTIVE SIZE SEARCH -> EXACT GAS -> ALL COSTS -> WORST-CASE NET PNL -> FINAL REQUOTE -> PREFLIGHT -> GOVERNOR -> CONTROLLED SIGNER -> PRIVATE SUBMIT -> RECEIPT -> INDEPENDENT REALIZED PNL -> LEARN -> RESCAN`

The fixed elements are policy and safety rules.

The variable elements are market observations.

## 11. Formula freeze rule

When the architecture reaches a verified profitable opportunity, do NOT freeze the winning pair, loan amount, fee tier, or block.

Freeze:

- economic formula
- proof schema
- safety invariants
- authorization rules
- provider selection policy
- dynamic sizing algorithm
- state-lock/requote requirements
- failure/rollback semantics

Keep market parameters dynamic.

A winning trade is evidence that the search-and-proof process worked; it is not a permanent trading recipe.

## 12. Safety / security requirements

- No live execution from a gross-positive observation alone.
- No gas-as-percentage model.
- No static loan size overriding live liquidity.
- No provider treated as permanent authority by default.
- No public relay fallback where private submission is required.
- No signer authority inferred from repository tests.
- No cross-block route stitched from incompatible observations.
- No ML/AI model may replace exact on-chain quote or economic proof.
- Any mismatch freezes the affected lane.
- Every failed lane follows FAIL -> FREEZE -> FORENSIC -> PATCH -> REGRESSION -> VERIFY.

## 13. Integration order

Phase A: retrofit dynamic gas + live Aave premium + liquidity-derived loan upper bounds.

Phase B: integrate adaptive exact loan optimizer with live route quotes.

Phase C: expand RPC provider registry/health scheduler and bounded task routing.

Phase D: integrate strategy expansion through one adapter at a time.

Phase E: connect complete EconomicProof to final requote and EVM preflight.

Phase F: production authority, signer, private relay, identical-artifact shadow, controlled execution and realized PnL.

No phase may bypass a higher-priority safety gate.

## 14. Evidence references

- Uniswap Developers, Fees: https://developers.uniswap.org/docs/get-started/concepts/fees
- Uniswap Developers, V3 pool data: https://developers.uniswap.org/docs/sdks/v3/guides/pool-data
- Aave V3 Pool source: https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/pool/Pool.sol
- Aave V3 flashloan logic: https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/logic/FlashLoanLogic.sol
- EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
- Polygon RPC provider guidance: https://support.polygon.technology/support/solutions/articles/82000902400-we-are-building-a-project-that-involves-reading-data-from-the-blockchain-can-polygon-provision-us-an
- Polygon public RPC deprecation notice (2026): https://forum.polygon.technology/t/deprecation-of-polygons-public-rpc-endpoints-mainnet-amoy/22014

## Final rule

> **Maximize dynamic market awareness. Minimize hardcoded market assumptions. Keep safety and proof deterministic.**
