# PHANTOMX S1 COVERAGE REPAIR EVIDENCE • 2026-09-21

## Triggering evidence
- S1 run #40 / ID `35574659400`
- Scanner HEAD: `af93d56fd7c1cf7b6cb2dd494abb8cffc542752f`
- Artifact: `phantomx-s1-qsv3-live-scan`
- Artifact ID: `10628135169`
- Artifact SHA-256: `14454f8b543373add880767f55f1f5c2f6048f27b4660ebc48b8589ddbc70a73`

## Finding
The S1 scanner returned success whenever the RPC pool produced a result, even though tile-level route evaluation could remain `UNAVAILABLE_OR_FAILED`.
Run #40 contained:
- 36 declared fee/pair tiles
- 28 successful tiles
- 8 `UNAVAILABLE_OR_FAILED` tiles
- 1,120 route observations
- 0 gross-positive observations
- dynamic Aave USDC ceiling: 596,890 USDC
- flash premium observed: 5 bps
- economic certification: `NOT_PERFORMED`
- profit claim: `NONE`

Therefore run #40 is incomplete coverage evidence and cannot support a market-negative or exhaustion conclusion.

## Root cause
S1 directly executed both directions inside a broad exception handler and appended unresolved tiles, but did not use the canonical opportunity-discovery failure model or a complete tile-coverage gate.

## Surgical repair
The S1 scanner now:
1. evaluates each direction through the canonical exact-discovery boundary;
2. retains exact failure evidence;
3. retries only failures classified as infrastructure/retryable;
4. treats semantic execution reverts as terminal outcomes;
5. classifies each tile as `COMPLETE`, `COMPLETE_NO_COMMON_ROUTE`, or `PARTIAL_INCOMPLETE`;
6. exposes aggregate coverage status;
7. exits non-zero when any declared tile remains incomplete.

## Verification
- Phase-19 run #969 / ID `35576798169` completed GREEN on final repair HEAD `2269aaab5813c04a3f30cc05ac4c6833846a65d5`.
- The GREEN run included Solidity compilation, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the full Phase-19 unittest suite.
- Regression coverage verifies incomplete coverage is rejected, terminal no-common-route can be accepted when all evaluations are accounted for, and complete common-route evidence is accepted.
- Corrected S1 run #45 / ID `35576798186` targets the repaired lineage and is queued behind an older in-flight S1 run; its result is the next admissible S1 market evidence.

## Safety
LIVE SIGNING = BLOCKED
PUBLIC BROADCAST = BLOCKED
LIVE CAPITAL = LOCKED
