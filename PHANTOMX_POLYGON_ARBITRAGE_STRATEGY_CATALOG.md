# PHANTOMX Polygon Arbitrage Strategy Catalog

## Purpose

This catalog defines the complete discovery search space for the Polygon PoS MVP.
It separates:
1. market graph coverage,
2. strategy generation,
3. deterministic economic proof,
4. execution certification.

Registration or discovery never authorizes production execution.

## Current market-informed venue scope

The live Polygon DEX landscape currently includes, among others, Uniswap V4, Ramses V3, Uniswap V3,
QuickSwap, QuickSwap V3, Balancer V2, SushiSwap V3, Curve, Uniswap V2 and additional smaller
venues. Current public market dashboards show material Polygon activity across these venue families,
while smaller venues remain discoverable candidates rather than being silently excluded.

The system therefore uses a two-layer venue policy:
- discovery inventory: all on-chain venues that can be enumerated and satisfy safety metadata;
- execution registry: only independently certified adapters.

## Strategy families

### S0 — Direct two-venue cross-venue A->B->A
Two venues, two legs, same asset returned to the flash-loan asset.
Status: canonical direct family.

### S1 — CLMM vs CLMM direct
QuickSwap V3, Uniswap V3, Ramses V3, SushiSwap V3 and other compatible concentrated-liquidity venues.
Search dynamic pool fee/tick configuration rather than assuming a fixed fee grid.

### S2 — V4 vs V3 / V2
Uniswap V4 pools against V3/V2 venues.
Hookless pools first. Hooked pools require separate hook semantics and adversarial certification.

### S3 — V2-style vs CLMM
QuickSwap V2, Uniswap V2, SushiSwap-style pools, Ramses volatile pools and compatible V2-like venues
against CLMM venues.

### S4 — Curve / stable-swap vs AMM
Curve and compatible stable/correlated pools against V2/V3/V4 venues.
Search both direct stable pairs and underlying-token routes.

### S5 — Balancer weighted/stable pools vs AMM
Balancer V2 queryBatchSwap-style exact routes against AMM venues.
Requires exact route quoting and vault semantics.

### S6 — Triangular 3-leg
BASE -> A -> B -> BASE.
Enumerate every eligible bridge pair and every certified venue permutation.

### S7 — Four-leg bounded cycles
BASE -> A -> B -> C -> BASE.
Use simple-cycle enumeration with deterministic de-duplication.
Execution remains discovery-only until a dedicated multi-leg executor is certified.

### S8 — Stablecoin depeg cycles
Stablecoin graph across USDC.e/USDC variants, USDT variants, DAI and other eligible stable assets.
Do not assume $1 parity. Use live settlement valuation.

### S9 — Same-venue multi-pool / fee-tier dislocation
Two independently usable pools on the same protocol can create a cycle even without a second DEX.
This includes V3 fee-tier differences and multiple pools for the same asset pair.

### S10 — Split-route / multi-pool optimization
Split one flash-loan input across multiple pools and recombine output.
The optimizer must solve exact integer allocation over the eligible pool graph and include every
incremental gas and swap fee.

### S11 — Cross-curve shape arbitrage
V2 constant-product vs concentrated-liquidity vs stable-swap vs weighted-pool curves.
The edge is the temporary difference in executable price curves, not merely displayed spot price.

### S12 — Post-state-change/event-driven arbitrage
When a new pool, liquidity addition/removal, large swap or fee-state change is observed, immediately
re-evaluate affected graph neighborhoods. This increases opportunity frequency without permanently
dropping cold routes.

### S13 — New-pool initialization window
Newly created pools receive a burst discovery window once runtime safety checks prove:
code identity, token metadata, liquidity, swapability, and anti-tax/anti-reentrancy constraints.

### S14 — Cross-venue correlated-asset cycles
Examples include wrapped/native representations, liquid staking representations and correlated
stable assets. Correlation is only a search heuristic; exact quotes determine truth.

### S15 — Alternative flash-liquidity variant
Aave V3 remains the canonical source. Other atomic liquidity sources can be researched as variants,
but each needs independent callback, repayment, fee and executor certification.

### S16 — Post-trade backrun / state-dislocation research
Look for executable price dislocations immediately after large confirmed state changes.
This is discovery-first and requires stricter timing, MEV-risk and private-relay controls before
any execution consideration.

### S17 — V4 hook-aware arbitrage
Hooked V4 pools are searched only after the hook contract's state transitions and permissions are
proven. A route cannot infer hook behavior from pool price alone.

### S18 — Cross-protocol atomic composability
Atomic sequences involving DEX plus a protocol action are considered only when the action is
deterministic, reversible inside the transaction, and its exact cost/risk can be incorporated into
EconomicProof.

### S19 — Oracle/market-price divergence as a detector
External/oracle prices may be used as a detector or ranking signal, never as executable truth.
Execution truth remains exact on-chain route output and final state lock.

## Universe enumeration model

The Polygon market is represented as a directed graph:

TOKEN nodes
POOL edges
VENUE metadata
FEE/TICK/HOOK state
LIVE LIQUIDITY
PINNED BLOCK
QUOTE CAPABILITY
GAS CAPABILITY
RISK FLAGS

For every eligible pool edge, the system records one of:
- QUOTED
- ONCHAIN_UNAVAILABLE
- RISK_REJECTED
- ECONOMIC_REJECTED
- RPC_EXHAUSTED
- ADAPTER_UNAVAILABLE

RPC_EXHAUSTED is never converted into NO_OPPORTUNITY.

## Pair universe policy

The old hand-selected pair list remains a smoke-test seed only.
The production discovery universe is generated from the live pool graph.

Token admission stages:
1. contract/code validity;
2. decimals/metadata validity;
3. transferable/swappable behavior;
4. liquidity threshold;
5. known token-tax/fee-on-transfer detection;
6. flash-loan asset compatibility;
7. economic relevance;
8. exact venue-edge enumeration.

Every admitted token must be searchable through all registered venue families where a pool edge exists.

## Exhaustion levels

### L0 — Seed universe
Known majors/stables and existing certified smoke pairs.

### L1 — Registered-venue universe
All tokens/pools found on currently registered venues.

### L2 — Full eligible Polygon DEX universe
Every discovered venue adapter, every eligible pool edge, every supported fee/tick/hook state.

### L3 — Bounded graph universe
All simple cycles up to the configured maximum leg count with exact deterministic generation.

### L4 — Continuous hunt
L0-L3 are continuously refreshed. New pools and state changes create incremental re-search tasks.

The MVP target is L4 with execution certification restricted to independently proven route families.

## Opportunity-frequency engine

Each graph element receives a scheduling class:

HOT:
- recently positive,
- newly initialized,
- recently changed liquidity,
- recent large state change.

WARM:
- liquid active pools with recurring cross-venue divergence.

COLD:
- eligible but historically quiet routes.

No class permanently excludes a route.

The scheduler spends the RPC budget first on HOT/WARM tasks, then guarantees periodic COLD coverage.
This increases speed without sacrificing eventual completeness.

## Completion criteria

A strategy family is discovery-complete only when:
- its venue adapters can enumerate relevant pools;
- all supported parameter states are enumerated;
- all directed route forms are generated;
- every generated task reaches a terminal evidence state;
- RPC_EXHAUSTED tasks are requeued;
- the final universe snapshot has reproducible block/provenance hashes.

A strategy family is execution-certified only after:
quote -> economics -> exact gas -> final requote -> state lock -> EVM preflight -> Governor ->
authority -> signer -> private relay -> receipt -> independent realized PnL > $0.20.

## Current design rule

Do not add more arbitrary pair constants when the correct next unit is:
DISCOVER POOLS -> BUILD GRAPH -> ENUMERATE EDGES -> GENERATE ROUTES -> QUOTE -> PROVE ECONOMICS.

