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
