# PHANTOMX EXECUTION PLAN LOCK
# MISSION CONTROL - FROZEN ROADMAP
# Version: 1.0
# Locked: 2026-09-22
# Repository: manish91082-coder/ghost-hunter-new
# Branch: phase-19-e2e-harness
# Scope: Polygon PoS only, Chain ID 137

## 1. MISSION OBJECTIVE

This roadmap is now the sole execution lane for the active PHANTOMX / FLASH LOAN GHOST HUNTER mission.

Mission goal:
Build an evidence-backed Polygon flash-loan arbitrage system that can progress from real opportunity discovery to exact route economics, deterministic execution preparation, controlled execution, settlement reconciliation, and proof that realized net profit is strictly greater than $0.20 after all applicable costs.

The project is NOT considered complete merely because code compiles, tests pass, a read-only hunt returns observations, a gross-positive quote exists, a fork succeeds, or a historical observation looks profitable.

Production completion requires the full evidence chain and a realized on-chain result satisfying the strict economic invariant.

## 2. SCOPE LOCK

Current blockchain scope is intentionally fixed to:

- Polygon PoS
- Chain ID 137

No multi-chain expansion is permitted during this locked roadmap.

Current declared route venues remain limited to the implemented Polygon adapters:

- QuickSwap V2
- QuickSwap V3
- Uniswap V3
- Uniswap V4
- Ramses V3
- Curve

Flash liquidity remains Aave V3.

Static First-Hunt core pair surface remains the declared 9 USDC-based pairs:

- USDC/WETH
- USDC/WPOL
- USDC/WBTC
- USDC/DAI
- USDC/LINK
- USDC/AAVE
- USDC/UNI
- USDC/USDT.e
- USDC/MIMATIC

Dynamic discovery is allowed where the strategy specification explicitly requires it.

## 3. NON-NEGOTIABLE SAFETY INVARIANTS

1. LIVE SIGNING = BLOCKED until all production authority gates are independently accepted.
2. PUBLIC BROADCAST = BLOCKED.
3. LIVE CAPITAL = LOCKED.
4. No private keys, seeds, keystore passwords, relay credentials, authentication secrets, raw signed transactions, or secret material in the certification workspace.
5. Read-only live-market work must remain read-only.
6. A queue or in-progress workflow is never GREEN.
7. A cancelled, superseded, stale, partial, or artifact-less run is never a market certificate.
8. Stale-head evidence cannot certify newer code.
9. Incomplete coverage cannot be relabeled as no-route or negative-market evidence.
10. Reasoned semantic execution reverts remain terminal unless the strategy specification explicitly defines another safe semantic interpretation.
11. Ambiguous transport/provider failures may be retried only inside the bounded, explicitly scoped recovery boundary.
12. EconomicProof is separate from discovery success.
13. Realized net profit must be strictly greater than $0.20 after all applicable costs.
14. No profitability claim is accepted from gross delta alone.
15. No production authorization is inferred from unit tests or fork tests.
16. The master branch is not to be modified by this execution lane.
17. No unrelated repository cleanup, feature work, refactoring, cosmetic work, or scope expansion is permitted.

## 4. OPERATING DOCTRINE

Every Next cycle follows exactly:

INSPECT -> VERIFY -> DECIDE -> IMPLEMENT -> TEST -> PUSH -> GITHUB STATE CHECK -> CI TERMINAL RESULT -> VERIFIER -> ADVANCE

Rules:

- Evidence beats narrative.
- Exact SHA beats memory.
- Terminal state beats expectation.
- Artifact beats console interpretation.
- Current tree beats historical assumptions.
- Current-head evidence beats older evidence.
- One strategy lane at a time for live-market evidence.
- Independent deterministic preparation may be parallelized only when it cannot alter, cancel, overlap, or contaminate the active market-hunt lane.
- Never wait blindly. Every continuation cycle actively checks workflow state, jobs, artifacts, exact head, and blocking cause.
- Every repository mutation is followed by exact-head and CI verification.
- A failure becomes a repair task, not a reason to skip the gate.
- A GREEN deterministic CI result is necessary, but not sufficient, for market certification.
- A market certificate is never sufficient for production authorization.

## 5. SPEED WITHOUT RISK

Speed is achieved by eliminating avoidable idle time, not by skipping verification.

Allowed acceleration:

- Use depth-first work so the active strategy reaches a terminal state before moving to the next strategy.
- Prepare deterministic tests and evidence schemas in advance when they do not touch the active market scanner.
- Use bounded RPC failover and circuit-breaking rather than uncontrolled provider fan-out.
- Use one active market hunt per shared market-hunt concurrency domain.
- Poll exact workflow state and artifact availability at every continuation cycle.
- Reuse verified test infrastructure and evidence contracts.
- Avoid repeated status-only commits unless a durable state transition needs recording.
- Batch independent inspection reads into one control-room cycle.
- Repair the smallest proven root cause instead of making broad policy changes.

Not allowed:

- Launching overlapping market hunts merely to appear faster.
- Expanding a search space silently to force a positive outcome.
- Shrinking a declared search space to fit runtime.
- Treating timeout as a market result.
- Converting unavailable data into no-route proof.
- Declaring GREEN while any required stage is queued, running, cancelled, skipped unexpectedly, or otherwise non-successful.
- Moving to the next strategy while the current strategy has an unresolved certification gate.

## 6. MASTER PHASE ROADMAP

### PHASE 0 - MISSION / GOVERNANCE FREEZE
Subtasks:
0.1 Freeze Polygon-only scope.
0.2 Freeze safety invariants.
0.3 Freeze strict realized net > $0.20 rule.
0.4 Freeze evidence-first certification semantics.
0.5 Freeze depth-first strategy order.
0.6 Freeze current branch discipline and master protection.
Exit gate:
- Durable lock exists in GitHub.
- Current live branch/head verified.
- Active workflow state verified.

### PHASE 1 - S5 CURRENT RUN TERMINALIZATION
Subtasks:
1.1 Inspect S5 #34 exact head, run state, jobs, and steps.
1.2 Wait by verification cycles only, never blind waiting.
1.3 On terminal, retrieve artifact.
1.4 Verify artifact identity, digest, exact scanner head, pinned block and coverage.
1.5 Inspect dynamic pair-universe status.
1.6 Inspect every Curve registry lane.
1.7 Inspect every UV3 fee tier and direction.
1.8 Inspect RPC failure ledger and retry classification.
1.9 Inspect gross and post-flash observations.
1.10 Determine whether the run is COMPLETE, PARTIAL_INCOMPLETE, or FAILED.
1.11 Repair only a proven root cause.
1.12 Re-run only from a verified current engineering head.
Exit gate:
- S5 is certified for its declared bounded domain, OR
- a precise blocker/repair is recorded and the repair is verified.

### PHASE 2 - POLYGON UNIVERSE FOUNDATION
Subtasks:
2.1 Verify current-block inventory sources.
2.2 Verify historical fixed-snapshot campaign.
2.3 Verify venue registry and factory enumeration coverage.
2.4 Verify pool discovery provenance.
2.5 Verify duplicate/alias handling.
2.6 Verify recent-window dynamic pair surface.
2.7 Verify historical continuation cursor integrity.
2.8 Distinguish ONCHAIN_UNAVAILABLE from confirmed no-pool.
2.9 Define snapshot saturation criteria.
2.10 Define continuous/event-driven re-scan semantics.
Exit gate:
- The universe model has explicit completeness semantics.
- Historical and current-block evidence cannot be conflated.

### PHASE 3 - S0 DEPTH-FIRST
Subtasks:
3.1 Current-head refresh.
3.2 9 pair x 4 UV3 fee matrix.
3.3 Both directions.
3.4 Dynamic Aave loan frontier.
3.5 Complete tile accounting.
3.6 Retryable RPC recovery.
3.7 Exact quote evidence.
3.8 Gross delta.
3.9 Post-flash delta.
3.10 Cost model.
3.11 EconomicProof path.
3.12 Final requote/state lock.
3.13 EVM preflight.
3.14 Fork execution evidence.
3.15 Regression suite.
3.16 Live read evidence.
Exit gate:
- S0 evidence bundle complete for its declared bounded domain.
- No hidden incomplete cells.

### PHASE 4 - S1 DEPTH-FIRST
Subtasks:
4.1 Refresh current head.
4.2 QuickSwap V3 <-> Uniswap V3.
4.3 9-pair matrix.
4.4 4 UV3 fees.
4.5 Both directions.
4.6 Full failure retention.
4.7 Coverage certificate.
4.8 Economic evaluation.
4.9 Adversarial verification.
4.10 EVM/fork evidence.
4.11 Live read evidence.
Exit gate:
- S1 complete or a precisely isolated blocker is repaired and re-verified.

### PHASE 5 - S2 DEPTH-FIRST
Subtasks:
5.1 Refresh current head.
5.2 5 declared seed pairs.
5.3 Uniswap V4 fee tiers: 100, 500, 3000, 10000.
5.4 Tick spacings: 1, 10, 20, 60, 100, 200.
5.5 UV3 fee side per current contract.
5.6 Both directions.
5.7 Hookless baseline only in S2.
5.8 Complete parameter/tile coverage.
5.9 Economic evaluation and adversarial checks.
5.10 EVM/fork verification.
5.11 Live read verification.
Exit gate:
- S2 bounded evidence is complete and current-head verified.

### PHASE 6 - S3 DEPTH-FIRST
Subtasks:
6.1 7 declared pairs.
6.2 Ramses tick spacings: 1, 5, 10, 50, 100, 200.
6.3 UV3 fee tiers.
6.4 Both directions.
6.5 Distinguish deterministic missing pool from unresolved RPC evidence.
6.6 Complete 168-cell declared matrix.
6.7 Quote and economics.
6.8 EVM/fork and adversarial tests.
6.9 Live read verification.
Exit gate:
- Complete S3 bounded certification.

### PHASE 7 - S5 + S5A DEPTH-FIRST
Subtasks:
7.1 Complete S5 current dynamic pair lane.
7.2 Certify six Curve registries.
7.3 Certify Curve pool resolution semantics.
7.4 Certify UV3 fee matrix and directions.
7.5 Complete dynamic pair-surface evidence.
7.6 Complete S5A focused Curve/MAI probe as an auxiliary diagnostic.
7.7 Keep S5A explicitly non-production and non-universe-complete.
7.8 Complete economics and adversarial checks.
Exit gate:
- S5 certified for its declared bounded dynamic domain.
- S5A diagnostic status recorded separately.

### PHASE 8 - S9 DEPTH-FIRST
Subtasks:
8.1 7 declared pairs.
8.2 QuickSwap V2 <-> Ramses V3.
8.3 Ramses tick-spacing matrix.
8.4 Both directions.
8.5 Complete coverage classification.
8.6 Economics and adversarial tests.
8.7 Live read verification.
Exit gate:
- S9 certified or precisely blocked.

### PHASE 9 - S10 DEPTH-FIRST
Subtasks:
9.1 7 declared pairs.
9.2 QuickSwap V3 <-> Ramses V3.
9.3 Complete spacing/fee/direction matrix.
9.4 Preserve gross-positive evidence without overstating profitability.
9.5 Post-flash economics.
9.6 Adversarial and EVM/fork checks.
9.7 Live read verification.
Exit gate:
- S10 certified or precisely blocked.

### PHASE 10 - S6 TRIANGULAR DEPTH-FIRST
Subtasks:
10.1 7 bridge assets.
10.2 42 ordered bridge pairs.
10.3 3 venues: QSV3, Ramses V3, UV3.
10.4 6 venue permutations per ordered pair.
10.5 Parameterize 4 UV3 fees and 6 Ramses spacings where applicable.
10.6 Maximum theoretical parameterized topology: 6,048 before eligibility pruning.
10.7 Exact eligibility evidence.
10.8 Cycle correctness.
10.9 Economics and adversarial verification.
10.10 Fork execution proof.
10.11 Live read proof.
Exit gate:
- S6 declared topology space is fully accounted for under its eligibility semantics.

### PHASE 11 - X1 DEPTH-FIRST
Subtasks:
11.1 Same-venue UV3 fee dislocation.
11.2 Ordered distinct in/out fee pairs: 12 per pair.
11.3 9 core pairs.
11.4 108 raw fee-pair combinations.
11.5 Both directional economics where defined.
11.6 Coverage certificate.
11.7 EconomicProof.
11.8 Adversarial/EVM/fork evidence.
11.9 Live read evidence.
Exit gate:
- X1 bounded lane certified.

### PHASE 12 - X2 THROUGH X13 EXPANSION
For each X strategy, depth-first:
12.A Define strategy contract and family.
12.B Define eligible pair/token graph.
12.C Define pool inventory.
12.D Define parameter matrix.
12.E Define route topology.
12.F Implement adapter/composer if missing.
12.G Implement fail-closed failure semantics.
12.H Add deterministic regression tests.
12.I Run Phase-19 exact-head verification.
12.J Run bounded live read.
12.K Perform artifact forensic analysis.
12.L Perform economics.
12.M Perform adversarial/EVM/fork verification.
12.N Certify or repair.
No X strategy may be treated as production-capable solely because it is registered.

### PHASE 13 - GLOBAL ROUTE SATURATION
Subtasks:
13.1 Reconcile all declared venue adapters.
13.2 Verify all directionality.
13.3 Verify all strategy family graph cycles.
13.4 Detect duplicate route representations.
13.5 Verify no silent hard caps.
13.6 Verify route eligibility pruning.
13.7 Verify missing-pool versus unavailable-data semantics.
13.8 Produce route coverage certificate.
Exit gate:
- No declared strategy family remains accidentally unreachable because of an infrastructure or orchestration omission.

### PHASE 14 - DYNAMIC LOAN UNIVERSE
Subtasks:
14.1 Live Aave reserve liquidity.
14.2 Flashloan premium.
14.3 Safety headroom.
14.4 Venue liquidity/price impact constraints.
14.5 Repayment constraints.
14.6 Integer loan-size domain.
14.7 Tie resolution.
14.8 Full supplied domain evaluation.
15.1 Reject mixed-block candidates.
Exit gate:
- Loan universe is explicit, live-derived, bounded, deterministic and fail-closed.

### PHASE 15 - ECONOMIC PROOF
Subtasks:
15.1 Exact execution gas estimate.
15.2 Effective gas price evidence.
15.3 Native/USD valuation evidence.
15.4 Swap and price-impact costs.
15.5 Flashloan premium.
15.6 Relay/MEV cost where applicable.
15.7 External operational costs.
15.8 Exact USDC settlement.
15.9 Strict net > $0.20.
15.10 Bind all components into hash-bound EconomicProof.
15.11 Reject stale or mismatched valuation state.
Exit gate:
- A candidate can enter execution preparation only with a valid EconomicProof above the strict floor.

### PHASE 16 - FINAL STATE LOCK
Subtasks:
16.1 Final route lock.
16.2 Final valuation lock.
16.3 Final gas lock.
16.4 Final EconomicProof lock.
16.5 One exact block across required evidence.
16.6 Final requote.
16.7 Detect state drift.
16.8 Reject stale evidence.
Exit gate:
- One immutable execution candidate with internally consistent evidence.

### PHASE 17 - EVM PREFLIGHT
Subtasks:
17.1 Deterministic transaction assembly.
17.2 Calldata validation.
17.3 Allowance/authorization checks.
17.4 Nonce reservation semantics.
17.5 Governor policy checks.
17.6 Gas envelope.
17.7 Adversarial input checks.
17.8 Fork execution probe.
Exit gate:
- EVM execution path is deterministic and preflight-clean without signing or broadcast.

### PHASE 18 - SHADOW MODE
Subtasks:
18.1 Identical artifact chain.
18.2 No live signing.
18.3 No broadcast.
18.4 Shadow observation.
18.5 Route drift detection.
18.6 Economic drift detection.
18.7 Operational failure rehearsal.
18.8 Reconciliation.
Exit gate:
- Shadow/staging evidence matches the immutable engineering lineage.

### PHASE 19 - EXTERNAL PRODUCTION EVIDENCE
Subtasks:
19.1 Controlled signer identity proof.
19.2 Controlled Polygon provider authority proof.
19.3 Controlled private relay proof.
19.4 Controlled shadow/staging proof.
19.5 Immutable artifact lineage.
19.6 Independent verifier acceptance.
Exit gate:
- Every required external authority is evidenced and independently verifiable.

### PHASE 20 - CONTROLLED MAINNET EXECUTION
This phase begins only after all prior gates are closed.

Subtasks:
20.1 Select one EconomicProof-qualified candidate.
20.2 Re-read required live state immediately before authorization.
20.3 Re-run final state lock.
20.4 Governor authorization.
20.5 Sign only inside the approved boundary.
20.6 Submit only through the approved controlled route.
20.7 Do not use public broadcast fallback.
20.8 Capture transaction hash and exact pre/post state.
20.9 Reconcile receipt and settlement.
20.10 Compute realized net PnL from actual settlement.
Exit gate:
- Realized result is fully reconciled.

### PHASE 21 - ERROR-CORRECTION LOOP
For any failure after production gate opening:

21.1 Freeze further execution.
21.2 Preserve exact artifact, transaction, receipt and logs.
21.3 Classify failure.
21.4 Identify minimum proven root cause.
21.5 Apply surgical repair.
21.6 Add regression test.
21.7 Re-run deterministic CI.
21.8 Re-run bounded live-read validation.
21.9 Re-run final state lock.
21.10 Re-authorize only after all gates return GREEN.
21.11 Never hide a failure by changing acceptance criteria.

### PHASE 22 - CONTINUOUS AUTONOMOUS HUNTING
Only after proven production success:

22.1 Continuous current-block scanning.
22.2 Event-driven pool/pair refresh.
22.3 Dynamic loan sizing.
22.4 Adaptive RPC fleet.
22.5 Bounded strategy scheduling.
22.6 Opportunity quorum/evidence.
22.7 EconomicProof.
22.8 Final requote/state lock.
22.9 Governor.
22.10 Controlled execution.
22.11 Settlement reconciliation.
22.12 Realized PnL ledger.
22.13 Continuous independent audit.
22.14 Automatic fail-closed behavior on drift or uncertainty.

## 7. MANDATORY EVIDENCE BUNDLE FOR EACH STRATEGY

Every strategy must be able to produce and preserve:

01. Strategy specification
02. Pair universe certificate
03. Pool inventory certificate
04. Parameter matrix
05. Route matrix
06. Exact pinned block
07. RPC provenance
08. Exact quote observations
09. Failure ledger
10. Coverage certificate
11. Gross result summary
12. Post-flash result summary
13. Gas model
14. EconomicProof
15. Final requote/state lock
16. State-lock identity
17. Fork execution evidence
18. Regression suite result
19. Live-read evidence
20. Production-readiness evidence, when reached

Missing required evidence means the strategy is NOT CERTIFIED.

## 8. STRATEGY STATUS STATES

Only these strategy states are valid:

- NOT STARTED
- INCOMPLETE
- FAILED
- CERTIFIED

Production authorization is a separate state and cannot be inferred from CERTIFIED.

## 9. CURRENT START POSITION

At lock time:

- Active blockchain: Polygon PoS, Chain ID 137
- Active branch: phase-19-e2e-harness
- Current branch HEAD: 3247021d816521176b57eb43629de7a72a180f31
- Current S5 executable head: 855410b2096fc119eca09f75d3f2745edd47bf9c
- S5 #34 / run 35699186433: IN_PROGRESS
- S5 #34 is read-only
- Phase-19 #1044 / run 35699186442: SUCCESS on exact S5 executable head
- Current active market hunt count observed: one
- Production authorization count: zero
- Live signing: BLOCKED
- Public broadcast: BLOCKED
- Live capital: LOCKED
- Realized net > $0.20: NOT PROVEN

## 10. IMMEDIATE NEXT GATE

The next admissible action is not a new strategy.

It is:

S5 #34 terminal check -> job/step verification -> artifact retrieval -> artifact forensic inspection -> coverage/economic classification -> surgical repair if and only if required -> exact-head Phase-19 verification -> current-head S5 re-verification if required -> S5 certification decision -> then S0 depth-first.

No parallel new market-hunt lane may be launched while S5 #34 is active.

## 11. COMMAND DISCIPLINE

The operator command is:

NEXT

Each NEXT consumes one control-room cycle and must leave the repository in a more verified state.

A NEXT cycle must never:

- skip a gate,
- silently broaden scope,
- silently reduce coverage,
- claim GREEN from non-terminal state,
- use stale evidence,
- promote gross positivity to profitability,
- authorize signing,
- authorize public broadcast,
- unlock live capital,
- or advance to the next strategy with the current strategy unresolved.

## 12. DEFINITION OF MISSION COMPLETE

Mission completion requires all of the following:

A. Polygon strategy universe is accounted for under explicit saturation semantics.
B. Declared strategy families are implemented or explicitly proven out of scope.
C. Each active strategy has complete bounded evidence.
D. Exact current-market opportunity is genuine and executable.
E. Complete economics are bound in EconomicProof.
F. Final requote/state lock passes.
G. EVM preflight passes.
H. External signer/provider/private-relay authority is proven.
I. Shadow/staging evidence is proven.
J. Controlled mainnet execution is performed through the approved boundary.
K. Settlement is reconciled from on-chain evidence.
L. Realized net profit is strictly greater than $0.20 after all applicable costs.
M. Independent final audit passes.
N. No unresolved safety or provenance contradiction remains.

Anything less is progress, not mission completion.

## 13. LOCK STATEMENT

This document is the frozen roadmap for the active execution lane.

Until the mission-complete definition above is satisfied, no unrelated task is to enter the execution queue.

When a blocker appears, repair the blocker.
When evidence is incomplete, complete the evidence.
When a test fails, fix the proven cause.
When a market result is negative, record it honestly and continue searching.
When evidence is ambiguous, fail closed.
When the system is ready, prove it before authorizing anything.

MISSION TARGET REMAINS UNCHANGED:

REAL, EXECUTABLE, EVIDENCE-BACKED POLYGON FLASH-LOAN ARBITRAGE
WITH REALIZED NET PROFIT STRICTLY GREATER THAN $0.20 AFTER ALL APPLICABLE COSTS.

END OF LOCKED PLAN
