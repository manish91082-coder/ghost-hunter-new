# PHANTOMX S5 #47 FORENSIC - AMBIGUOUS REVERT PROVIDER-HEALTH REPAIR
# 2026-09-23

## Run identity
- Workflow: PHANTOMX S5 Curve Uniswap V3 Live Hunt
- Run: 35882243231 (#47)
- Exact HEAD: 183785170bdd7f96f2fc23d61eca557c1c754bb2
- Artifact: 10762506820
- Artifact SHA256: 945fb591777ad0d4991e681749f85dba03927f35cf7b926ab28c7f3e3b301f61

## Forensic facts
- Expected tiles: 164
- Complete: 14 COMPLETE + 16 COMPLETE_NO_COMMON_ROUTE = 30
- Incomplete: 134
- Observations: 532
- Gross-positive: 0
- Best gross: -4.452314 USDC
- Retryable failures: 1,339
- Terminal failures: 4,266
- Pair universe: COMPLETE_RECENT_WINDOW
- economic_certification: NOT_PERFORMED
- profit_claim: NONE
- This remains incomplete infrastructure evidence, not market-negative proof.

## Root cause
The S5 ambiguous-revert failover correctly excludes the failed provider from the current logical request and requires distinct-provider consensus before terminal classification. However, the same ambiguous semantic revert was still passed into the generic recoverable-failure circuit breaker. Under 8 concurrent workers and 1-request-per-provider limits, repeated route-semantic reverts drove providers into circuit-open/low-health states even though the providers were still usable for other logical reads.

Artifact evidence shows 1,194 retryable failures with a single-provider generic execution-reverted diagnostic. The remaining retryable population includes a smaller mix of rate-limit, historical-state, authentication/paid-plan and admission failures.

## Surgical repair
RPCSemanticRevertConsensusError remains terminal after two distinct providers independently reproduce the ambiguous revert. The repair records an ambiguous semantic revert for history/diagnostics but does NOT decrement provider health, increment consecutive transport failures, or open the provider circuit. The provider is excluded only from that one logical recovery pass.

## Safety boundary
No search-space, loan frontier, economics, signing, broadcast or capital behavior changed. Fail-closed coverage remains unchanged. The remaining retryable provider-local failures remain retryable and are not reclassified.