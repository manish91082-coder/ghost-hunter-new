# PHANTOMX S5 #48 FORENSIC • RPC CAPACITY REPAIR TARGET • 2026-09-23

## Run identity
- Workflow: PHANTOMX S5 Curve Uniswap V3 Live Hunt
- Run: #48 / `35888656857`
- Scanner HEAD: `f645f6ce7bf0e14784437970cb3a758e4590b289`
- Artifact: `10765085719`
- Artifact SHA-256: `ac5ec4c960d638ae3c55008f5c6e09b34b4e6d45e1218ec37fd040bd01bf3715`
- Duration: 1118.06s
- Read-only: yes
- Signing: false
- Broadcast: false
- Live capital: false

## Coverage result
- Declared tiles: 164
- COMPLETE: 14
- COMPLETE_NO_COMMON_ROUTE: 31
- PARTIAL_INCOMPLETE: 119
- Pair universe: COMPLETE_RECENT_WINDOW
- Observations: 532
- Gross-positive: 0
- Best gross: -4.452314 USDC
- Economic certification: NOT_PERFORMED
- Profit claim: NONE

This is incomplete infrastructure/evidence coverage, not market-negative evidence.

## Retryable population
- Retryable evaluations: 344
- Prior S5 #47 retryables: 1,339
- Reduction: 995 fewer retryable evaluations (~74.3%)
- Dominant residual: 257 logical reads received one ambiguous reason-less `execution reverted` while alternate providers were unavailable/quarantined at that instant.
- Other residual retryables include 403/429 endpoint failures and historical-state availability.

## Surgical repair
1. Replace deprecated keyless `polygon-rpc.com` with the current official public QuickNode endpoint `https://rpc-mainnet.matic.quiknode.pro`.
2. Treat historical-state availability as task-local rather than provider-wide temporary quarantine.
3. Preserve bounded failover, per-provider concurrency=1, ambiguous-revert two-provider consensus, fail-closed coverage, and all economic/safety locks.
4. Fresh S5 must run on the verified repair HEAD before S0 advancement.

## Safety
LIVE SIGNING = BLOCKED
PUBLIC BROADCAST = BLOCKED
LIVE CAPITAL = LOCKED
