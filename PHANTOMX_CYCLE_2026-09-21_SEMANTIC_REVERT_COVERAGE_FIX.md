# PHANTOMX CYCLE EVIDENCE • 2026-09-21
## Semantic-revert coverage classifier repair

### Trigger
First-Hunt #67 (run ID 35536094045) was re-inspected after the earlier RPC failover correction.

Observed failed atomic shards:
- fee 100 / pair 4: failure, `no complete pair/fee tier produced an exact route grid`
- fee 100 / pair 6: failure, `no complete pair/fee tier produced an exact route grid`
- fee 100 / pair 1: exit 2 after recording only 6 observations with coverage 1/1 at the tile layer
- fee 500 / pair 5: failure, `no complete pair/fee tier produced an exact route grid`

### Root cause
The RPC failover layer correctly classifies `execution reverted` as non-retryable. However, `phantomx/opportunity_discovery.py` independently classified every `RPCPoolError` as infrastructure-retryable before examining the semantic message. A reverted `eth_call` therefore re-entered the retry domain at the higher discovery layer.

This created a classification mismatch:
RPC layer = terminal semantic failure
Discovery layer = retryable infrastructure failure

That mismatch prevented a fully accounted, no-common-route tile from reaching `COMPLETE_NO_COMMON_ROUTE` and could escalate to shard-level incomplete/failure.

### Repair
Commit `014e14ed25859a80d0f057c3e6de76adac1d4cb3`:
- checks the exception message for `execution reverted` before the infrastructure-type shortcut;
- preserves semantic EVM reverts as terminal market/call evidence;
- keeps genuine transport/rate-limit/time-out errors retryable.

Commit `864f45b9418cf019bd4f6ab1acda4bb2bd565f21`:
- adds regression coverage proving semantic `RPCPoolError` reverts are terminal;
- adds a transport 429 regression proving legitimate retry behavior remains intact.

### Verification state
GitHub commit diffs for both repair commits were independently fetched and match the intended changes.
Combined commit status endpoints currently report no published status checks for these commits yet. Therefore CI GREEN is not claimed in this evidence file.

### Safety / mission status
- Read-only First-Hunt path remains non-signing and non-broadcasting.
- No live capital is enabled.
- No profitability certificate is created by this repair.
- The correct next market step is a fresh 36-cell First-Hunt after the repair lineage is CI-verified.
- A fresh hunt result must still satisfy all 36 atomic shards and all 36 pair/fee tiles before it can be treated as complete coverage.
