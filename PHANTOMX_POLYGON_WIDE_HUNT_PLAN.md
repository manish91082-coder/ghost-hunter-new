# PHANTOMX Polygon-Wide Hunt Expansion Plan

## Objective

Move from a handful of hand-selected live-read scanners to an exhaustive, continuously
resilient Polygon arbitrage discovery fabric while preserving the existing deterministic
economic and execution gates.

The goal is not to maximize raw quote count. The goal is to maximize the probability that
a genuinely executable opportunity is observed and then proven through the existing
EconomicProof -> final state lock -> EVM preflight -> Governor chain.

## Workstream A — RPC resilience first

### A1. Free-provider inventory

Maintain a replaceable registry of public/no-key Polygon endpoints. Public endpoints are
candidate infrastructure, not trusted truth. Every provider must pass runtime chain and
freshness probes before entering the active pool.

### A2. Task-preserving failover

A route candidate gets a stable hunt_task_id and market_block_context. Provider failure
must change only the provider assignment, never delete the route. Recoverable transport
failures include rate limits, timeouts, 5xx/gateway errors, connection failures and known
historical-state availability failures.

Semantic route errors such as an actual EVM execution revert are not retried blindly.

### A3. Block continuity

The pool first establishes a valid Polygon block. Subsequent reads carry the same explicit
block tag whenever the method supports it. If a provider cannot serve that historical block,
the same task rotates to another provider. If the whole pool cannot serve the pinned block,
the task is re-pinned as a new market observation cycle and is never silently mixed.

### A4. Health and scheduling

Track success rate, latency, last known head, consecutive failures, cooldown and circuit state.
Use a bounded active subset for normal operation, but allow sequential provider exhaustion on a
single failed logical read so route coverage is not lost because of one provider.

### A5. Free-tier economics

Prefer no-key public endpoints first. Do not add paid providers to the baseline MVP.
Providers that require keys or show unstable capabilities remain optional external lanes.

## Workstream B — Polygon universe discovery

### B1. Canonical inventory

Build a live token/pool inventory from on-chain factory registries and known protocol
deployment registries, retaining provenance for chain, contract address, block and discovery source.

### B2. Asset classes

Discover:
- majors: POL/WPOL, WETH, WBTC, stablecoins
- protocol/governance assets
- liquid LST/LRT and wrapped assets where Polygon liquidity exists
- bridged stablecoins and bridged majors
- long-tail assets only after minimum liquidity and safety screens

### B3. Venue inventory

Current code already has adapters for QuickSwap V2/V3, Uniswap V3/V4, Ramses V3 and Curve,
plus discovery placeholders for Balancer. The next phase makes the venue registry dynamic and
adds protocol-specific pool enumeration rather than relying on fixed pair lists.

### B4. Pair graph

Represent each token as a graph node and each executable pool as a directed edge. A pair is
not considered searched until every relevant venue edge has either produced a quote at the
pinned block or returned an explicit, provenance-backed unavailable reason.

## Workstream C — Strategy-complete graph search

Run strategy families in this order:

1. Direct two-venue A->B->A across every certified venue pair.
2. Same-venue fee-tier / pool-selection arbitrage where distinct pools can create a cycle.
3. Stablecoin depeg / stable-stable cycles.
4. 3-leg triangular cycles.
5. 4-leg bounded graph cycles.
6. Mixed AMM curve-shape routes (V2/V3/Curve/Balancer-style).
7. V4 hookless pools, then separately governed hooked pools.
8. Alternative flash-liquidity sources.
9. Event-driven strategies around newly created/updated pools, with stricter adversarial tests.
10. Cross-protocol composability opportunities that still fit a single atomic transaction.

AI may rank the candidate graph and choose search order. Deterministic quote, economics and
execution gates remain authoritative.

## Workstream D — Adaptive opportunity-frequency engine

Instead of rescanning everything at the same cadence:
- hot routes: rescan every block / immediately after material pool state change
- warm routes: rescan every small block window
- cold routes: rescan periodically
- newly discovered pools: burst scan
- recently profitable-but-rejected routes: high-priority recheck

Use opportunity history to prioritize work, not to exclude cold routes permanently.

Search scheduling is budgeted by RPC health and workload, not by a fixed endpoint count.

## Workstream E — Economic perfection

Every positive-looking gross route must pass:
exact dynamic loan ceiling -> final dense size search -> exact gas -> live POL/USD ->
Aave premium -> relay/MEV/risk bounds -> EconomicProof -> final requote/state lock.

Gross positive is never called profit.

## Workstream F — Execution completion

Promotion gates:
- direct two-leg strategy first
- 3+ leg execution only after dedicated executor/call-data/adversarial/fork certification
- signer identity proof
- Polygon authority proof
- private relay proof
- identical-artifact staging/shadow proof
- realized receipt/PnL proof > $0.20

## Exhaustion criterion

Polygon universe exhausted means no unsearched eligible graph element remains in the declared
inventory snapshot. It does not mean every economically impossible token pair was hammered forever.

A universe snapshot is complete only when:
1. token inventory was captured with block/provenance;
2. all eligible pools across registered venues were enumerated;
3. all directed edges were classified;
4. strategy generators produced all bounded cycles up to the configured max leg count;
5. every task reached terminal state (quoted, onchain_unavailable, rpc_exhausted,
   risk_rejected, or economic_rejected);
6. rpc_exhausted tasks are automatically re-queued in the next healthy cycle.

The system must never convert rpc_exhausted into no_opportunity.

## Definition of done for MVP

MVP is not considered complete because a scanner runs. It is complete only after:
- a genuine candidate is discovered;
- full EconomicProof shows conservative net > $0.20;
- final requote and state lock pass;
- EVM preflight and Governor pass;
- external signer/provider/private-relay/shadow gates pass;
- controlled execution settles;
- independent receipt-based realized PnL is > $0.20;
- final audit freezes the exact artifact lineage.
