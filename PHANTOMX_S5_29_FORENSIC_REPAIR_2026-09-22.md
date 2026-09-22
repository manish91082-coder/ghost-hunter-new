# PHANTOMX S5 #29 FORENSIC EVIDENCE AND RPC SEMANTIC REPAIR
Date: 2026-09-22
Mission: PHANTOMX / FLASH LOAN GHOST HUNTER
Strategy: S5 CURVE <-> UNISWAP V3
Branch: phase-19-e2e-harness

## 1. Terminal run
- GitHub Actions run: #29 / 35635495324
- Executed commit: dc2deb28cbffce2d48c41f5c124d347d84f649ca
- Result: FAILURE
- Failure was not treated as a market-negative certificate.
- Artifact: 10658431661
- Artifact digest: sha256:4abd04e03df1c4cff057c48ae3fb69f954877cc9bfbe837c806c0e392285cb3a
- Extracted JSON SHA-256: 376dc6ddc766e1e201b214cf64bc3db38975bd0394053742ec225bb9fa44e846
- Scanner duration: 3173.746 seconds
- Artifact provenance records the exact branch, commit and workflow run.

## 2. Observed result
- Pair-universe status: COMPLETE_RECENT_WINDOW
- Active pairs: 6
- Published tile records: 164
- Completed tiles: 20
- Incomplete tiles: 144
- Exact route observations: 640
- Gross-positive observations: 0
- Best gross delta: -5.019499 USDC
- Economic certification: NOT_PERFORMED
- Profit claim: NONE
- Read-only: true
- Signing: false
- Submission: false
- Broadcast: false
- Live capital: false

The result is PARTIAL_INCOMPLETE. It must not be described as complete S5 discovery evidence and must not be used as proof of Polygon-wide absence of opportunities.

## 3. Forensic root cause
The large incomplete set was dominated by raw execution reverted RPC errors recorded as non-retryable. The error had no concrete revert reason. Treating a reason-less revert as terminal prevents an independent RPC provider from determining whether the response is a true semantic route rejection or a provider-side loss of revert data.

Reasoned execution reverts remain terminal. A reason-less execution revert is ambiguous and is now eligible for the existing bounded provider failover. The special execution reverted: Unexpected error behavior remains recoverable.

## 4. Engineering repair
Commit chain:
- rpc repair: cbbcb34847813681016b136e92bc1a3031a83194
- regression tests: a24cb904b163c60490992124cd4df6f9474e5cee
- test expectation alignment: 92786f5aee2d5d397cf181fa685e0150bc6a7de3

The final repair classifies:
- reasoned EVM execution revert: terminal
- reason-less EVM execution revert: recoverable
- execution reverted: Unexpected error: recoverable
- transport, rate-limit and gateway failures: recoverable

## 5. Deterministic verification
Phase-19 #1029 / 35685369858 completed SUCCESS on 92786f5aee2d5d397cf181fa685e0150bc6a7de3.
All Solidity compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe and Phase-19 unit test stages completed successfully.

The preceding #1027 and #1028 failures are superseded verification attempts:
- #1027 failed because the regression suite still encoded the old generic-revert expectation.
- #1028 failed on the stale exhaustion-count expectation.
The final aligned repair was verified by #1029.

## 6. S5 next gate
A fresh isolated S5 read-only run must be launched only after the repaired lineage passes CI. The run must use the narrow .github/PHANTOMX_S5_KICK trigger and preserve exact-head provenance.

Acceptance remains:
- every observed tile accounted for
- no retryable failure left unresolved
- pair-universe status explicitly complete for the declared recent window
- economic certification kept separate from discovery
- no signing, broadcast or live capital

## 7. Safety
LIVE SIGNING = BLOCKED
PUBLIC BROADCAST = BLOCKED
LIVE CAPITAL = LOCKED
 
## 8. Scope correction after S5 #30
S5 #30 / run 35686104122 was launched from commit 0093e895e5815d0a848d056e0ca5d9641cb9a317 after the first reason-less revert repair. It failed before route tiles were emitted because Curve pair-surface discovery for USDC.e/WBTC encountered a reason-less execution revert across the bounded provider fleet.

Forensic conclusion: ambiguous-revert recovery cannot be enabled globally at the RPC transport boundary because Curve registry discovery legitimately uses some execution reverts as semantic no-match signals. The safe architecture is caller-scoped:
- default PolygonRPCFailoverPool.call keeps execution reverts terminal
- call_with_ambiguous_revert_failover is explicit and bounded
- Curve quote_snapshot uses the explicit path
- Uniswap V3 quote uses the explicit path
- Curve registry discovery and pool resolution remain on the default fail-closed path

This preserves semantic registry behavior while allowing quote reads to seek an independent provider result when revert data is missing.

The scoped architecture was verified by Phase-19 #1036 / 35687011135, which completed SUCCESS on commit 6853229b9079e52231534247197c8935f08ed52f. The full Phase-19 job, including Solidity compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe and the unittest suite, completed successfully.

S5 #30 remains evidence of an infrastructure/control-path failure and is not a market result. A fresh S5 run is required on the scoped architecture.
 
## 9. Discovery-layer retry classification correction
After the scoped RPC repair, the quote boundary correctly uses explicit ambiguous-revert failover. A second semantic gap was identified in phantomx/opportunity_discovery.py: an exhausted bounded provider recovery error contains the words execution reverted, and the previous classifier checked that phrase before recognizing that the RPC pool had already exhausted its recovery budget.

The final discovery classification now gives precedence to:
- all bounded Polygon RPC recovery passes failed: retryable unresolved infrastructure evidence
- reasoned execution reverted: terminal semantic evidence
- ordinary transport and rate-limit failures: retryable

Phase-19 #1039 / 35687559817 completed SUCCESS on 18c849f50a60e1b138fc6492740b070ee8de7868, including the full deterministic test suite.

S5 #31 / 35687323027 was started before this latest discovery-layer correction and remains evidence from the earlier scoped architecture only. It must not be relabeled as current-head evidence. A fresh S5 run is required after the correction.
