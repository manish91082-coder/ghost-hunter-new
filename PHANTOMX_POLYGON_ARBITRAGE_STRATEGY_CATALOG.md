# PHANTOMX Polygon Arbitrage Strategy Catalog

## Canonical existing strategy IDs

| ID | Search family | Current implementation state |
|---|---|---|
| S0 | QuickSwap V2 ↔ Uniswap V3 direct | Live read; canonical First-Hunt |
| S1 | QuickSwap V3 ↔ Uniswap V3 direct | Live read |
| S2 | Uniswap V4 ↔ Uniswap V3, hookless scope | Live read, discovery-only |
| S3 | Ramses V3 ↔ Uniswap V3 direct | Live read |
| S5 | Curve ↔ Uniswap V3 | Live read |
| S5A | Curve ↔ MAI exploratory probe | Existing probe |
| S6 | 3-leg triangular across QSV3/Ramses/UV3 | Live read, discovery-only |
| S9 | QuickSwap V2 ↔ Ramses V3 direct | Live read |
| S10 | QuickSwap V3 ↔ Ramses V3 direct | Live read |

## Planned expansion IDs

| ID | Family | Execution posture |
|---|---|---|
| X1 | Same-venue multi-pool / fee-tier dislocation | Discovery first |
| X2 | Split-route multi-pool allocation | Discovery first |
| X3 | Stablecoin and bridged-stable graph cycles | Discovery first |
| X4 | Bounded 4-leg cycles | Discovery first |
| X5 | Cross-curve V2/V3/V4/Curve/Balancer | Discovery first |
| X6 | Event-driven state-change rescans | Discovery first |
| X7 | New-pool initialization window | Discovery first |
| X8 | V4 hook-aware routes | Discovery first |
| X9 | Alternative flash-liquidity variants | Discovery first |
| X10 | Cross-protocol atomic composability | Discovery first |
| X11 | State-dislocation / backrun detector | Discovery first |
| X12 | Correlated wrapped/LST/stable asset cycles | Discovery first |
| X13 | Oracle divergence detector, never executable truth | Discovery first |

## Coverage model

The Polygon universe is represented as a graph:
TOKEN -> POOL EDGE -> VENUE/POOL PARAMETERS -> PINNED BLOCK -> QUOTE STATE.

A task is not searched until it reaches a terminal evidence status:
QUOTED, ONCHAIN_UNAVAILABLE, RISK_REJECTED, ECONOMIC_REJECTED, or ADAPTER_UNAVAILABLE.

RPC_EXHAUSTED is retryable and is never converted into NO_OPPORTUNITY.

## Expansion order

1. Refresh all existing S0/S1/S2/S3/S5/S6/S9/S10 lanes on resilient RPC.
2. Complete on-chain inventory for registered venues and turn every discovered pool into graph edges.
3. Dynamic pair universe replaces fixed hand-curated pairs.
4. Add X1 same-venue multi-pool search.
5. Add X3 stablecoin graph and X4 four-leg bounded cycles.
6. Add X5 mixed curve search.
7. Add X6/X7 event-driven/new-pool burst scheduling.
8. Add X8 hook-aware V4 only after hook-state safety certification.
9. Add X2 split-route optimization.
10. Add X9+ cross-protocol and alternative-liquidity research.

## MVP completion gate

No route is called profitable unless:
exact route quote -> dynamic loan bounds -> exact gas/costs -> final requote ->
EconomicProof -> EVM preflight -> Governor -> authorized signer -> private relay ->
receipt -> independent realized PnL > $0.20.

