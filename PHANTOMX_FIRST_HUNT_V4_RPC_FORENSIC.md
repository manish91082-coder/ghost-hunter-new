# PHANTOMX First-Hunt v4 RPC Forensic — Semantic Revert Exhaustion

## Trigger
First-Hunt v4 run #66 reached 33 valid shard results but failed the 36-cell completeness gate.

## Observed failure
The failed AAVE shard exhausted its failover pool with: RuntimeError: no complete pair/fee tier produced an exact route grid.
Its RPC history contained repeated eth_call semantic execution reverts mixed with transport and historical-state failures.
Two additional shards hit the 20-minute job ceiling while stuck in provider failover loops.

## Root cause
phantomx/rpc_failover.py classified any message containing execution reverted as recoverable. That made deterministic route/call rejections rotate through the entire 12-provider pool, even though the underlying request was semantically rejected by the contract.

## Policy correction
Transport, rate-limit, timeout, gateway and historical-state failures remain retryable. A contract-level EVM execution revert is semantic route evidence and is now non-retryable at the RPC failover boundary.

## Expected effect
- deterministic route rejection terminates locally;
- provider failover remains available for genuine infrastructure faults;
- shard runtime becomes bounded by useful evidence rather than semantic retry loops;
- First-Hunt coverage can distinguish COMPLETE_NO_COMMON_ROUTE from RPC_EXHAUSTED honestly.

## Verification requirements
1. Phase-19 deterministic tests must pass with execution reverts marked non-retryable.
2. A new First-Hunt kick must be run on the exact post-fix HEAD.
3. All 36 atomic fee/pair shards must produce valid evidence before the aggregate can become COMPLETE.
4. Any remaining RPC exhaustion stays incomplete and is never converted into no-opportunity.

## Safety
This change does not add signing, submission, broadcast, private relay access or live-capital authority.
