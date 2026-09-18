# PHANTOMX DYNAMIC MARKET AUTONOMY POLICY
## Canonical design directive

Purpose: make the MVP fully automatic while keeping every market-dependent value dynamic and every safety invariant deterministic.

### 1. Dynamic-by-default rule
Never freeze current market values in the decision path. Re-read current values for block, liquidity, fee configuration, quotes, price impact, gas, native-token USD price, relay cost, MEV/risk reserve, provider health, nonce, and deployed-runtime identity.
Only safety invariants and explicit policy bounds may be frozen.

### 2. Fee semantics
Uniswap V3 fee tiers are pool configuration values. The standard tiers are 0.01%, 0.05%, 0.30%, and 1.00%. The swap fee is charged on the input amount. A 1% tier is therefore a proportional swap cost, not a gas fee.
Formula: swap_fee_raw = floor(amount_in_raw * fee_tier / 1_000_000).
Gas is separate: gas_cost = gas_used * effective_gas_price, then converted using a live POL/USD valuation. Gas is not 1% of the loan amount.
The automatic economic gate must use transaction-attributable gas, not a percentage of loan size.

### 3. Aave flash-loan rule
The flash-loan premium is protocol state and must be read live for the exact asset and current market context. Do not hardcode an assumed Aave fee.
Authorized-borrower or other protocol-specific fee exceptions must be modeled from actual on-chain state, never assumed.

### 4. Dynamic loan-size rule
Do not start from a fixed loan amount.
safe_loan_ceiling = min(
  live Aave available flash liquidity after safety headroom,
  live route/pool input ceiling,
  live price-impact ceiling,
  optional system hard safety cap
)
A candidate above this ceiling is rejected before economic ranking.
Aave liquidity alone is insufficient: the DEX route must also be executable at the same pinned block and remain inside price-impact/liquidity constraints.

### 5. Optimization rule
Use a coarse-to-dense dynamic search:
live minimum -> coarse frontier -> neighborhood refinement -> exact economic certification.
The optimizer may claim an optimum only over the explicit evaluated domain. It must never silently turn a sampled domain into a continuous optimum claim.

### 6. Economic rule
WorstCaseNetPnL = final_settlement_value - loan_principal - flash_loan_premium - swap_fees - price_impact - gas - relay_cost - MEV/risk reserve - other transaction-attributable costs.
Execution eligibility requires WorstCaseNetPnL > $0.20.
Gross-positive is evidence, not profitability.

### 7. RPC fleet rule
Maintain a large provider inventory, potentially hundreds of entries, but never blast the whole inventory at once.
Polygon's official RPC reference lists multiple public and paid infrastructure providers and explicitly warns that public RPCs may have rate limits or traffic restrictions.
Each provider record should track endpoint, capability, published limits, observed latency, error/429 rate, latest block, chain ID, freshness, health score, cooldown, circuit state, and cost tier.
Critical reads use a small quorum. Large discovery workloads are chunked into independent tasks and distributed across healthy providers.

### 8. Rotation and overload control
Provider failure -> circuit open -> cooldown -> alternate provider.
429, timeout, or latency spike reduces concurrency for that provider.
Provider recovery increases concurrency only after measured headroom is restored.
Do not repeatedly retry the same request on the same failing provider.
Do not duplicate identical reads unless corroboration is required.

### 9. Strategy expansion rule
Current canonical strategy remains: Aave V3 flash liquidity + direct two-leg A->B->A across approved venues.
New venues, multi-hop routes, triangular routes, or additional flash-liquidity sources must enter through a strategy registry carrying quote, liquidity, fee, gas, risk, EconomicProof, preflight, and adversarial-test bindings.

### 10. Fully automatic loop
DISCOVER -> PIN BLOCK -> RPC QUORUM -> DISCOVER TOKENS/POOLS -> CHECK LIVE LOAN LIQUIDITY -> GENERATE SAFE LOAN DOMAIN -> ENUMERATE APPROVED STRATEGIES -> EXACT QUOTES -> ROUTE SIMULATION -> DYNAMIC GAS -> ALL COSTS -> EconomicProof -> STRICT > $0.20 -> FINAL REQUOTE -> STATE LOCK -> EVM PREFLIGHT -> GOVERNOR -> EXTERNAL AUTHORITY GATES -> CONTROLLED SIGNER -> PRIVATE SUBMISSION -> RECEIPT -> INDEPENDENT PnL -> LEARNING -> RESCAN.

### 11. Freeze vs dynamic
Freeze: safety rules, no-public-fallback, fail-closed behavior, evidence/provenance rules, hashing/binding rules, minimum profit invariant, audit schema.
Keep dynamic: token/pair selection, venue selection inside registry, pool, fee tier, loan size, liquidity ceiling, route direction, exact quotes, price impact, gas, POL/USD, flash premium, relay/MEV cost, provider selection, concurrency, chunk size, cadence, strategy ranking.

### 12. Integration sequence
DYN-1 Live Aave liquidity + flash-premium reader
DYN-2 Liquidity-aware loan-domain generator
DYN-3 Exact executor-path gas estimator
DYN-4 Live all-cost EconomicProof builder
DYN-5 Final requote/state lock
DYN-6 Strategy registry and venue expansion
DYN-7 Adaptive RPC fleet manager
DYN-8 Fully automatic scheduler
DYN-9 External authority gates
DYN-10 Controlled execution and independent realized-PnL audit

External references:
https://docs.polygon.technology/pos/reference/rpc-endpoints
https://developers.uniswap.org/docs/get-started/concepts/fees
https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/logic/FlashLoanLogic.sol
https://github.com/aave-dao/aave-address-book/blob/main/src/ts/AaveV3Polygon.ts
https://ethereum.org/developers/docs/gas/