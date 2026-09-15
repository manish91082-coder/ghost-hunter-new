# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. **STRICT RULE: synchronize this file on every assistant project response, without exception.** The synchronization must record the latest known branch HEAD/checkpoint, current phase/task, evidence actually observed, blockers, next action, and safety boundary. Never fabricate passes.

## 0. CURRENT RESUME CARD

- Project: PhantomX / Flash Loan Ghost Hunter
- Repository: `manish91082-coder/ghost-hunter-new`
- Default branch: `master`
- Active implementation branch: `phase-19-e2e-harness`
- Current branch HEAD: `05a9becc1542f6d588cbfc77691beacb8087f29b`
- Current HEAD commit: `ci(P19-CI-01): decouple status sync commits from verification triggers`
- Phase: Phase 19, execution-integrity / E2E policy harness
- Live mainnet execution: **BLOCKED**
- Live capital authorization: **BLOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## 1. NON-NEGOTIABLE RULES

Evidence first. Missing/contradictory evidence is UNKNOWN/BLOCKED.

Fail closed. No execution when quote, proof, simulation, authorization, nonce, signer, relay, authority, or settlement evidence is missing or inconsistent.

AI is advisory only and cannot override deterministic economics, EVM preflight, governance, authorization, or settlement truth.

Private execution has no public fallback.

Zero-cost means no mandatory paid infrastructure dependency. Gas and unavoidable execution costs remain real and must be modeled.

Live capital remains locked until all P0 gates have reproducible evidence.

**Status synchronization is mandatory on every project response.** A response is not considered complete until this file reflects the latest evidence-backed checkpoint.

## 2. CANONICAL PRODUCTION SPINE

`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

Initial scope: Polygon, Aave V3, QuickSwap V2, Uniswap V3, assets USDC/WETH/WMATIC/WBTC, direct two-leg `A → B → A`.

## 3. IMPLEMENTATION STATE AT THIS CHECKPOINT

Completed and under active integration/testing on Phase 19 include:

- strict realized-profit gate `net > $0.20`;
- all-in economic proof and exact-cost accounting;
- Ethereum Keccak-256 integrity hashing;
- immutable ExecutionIntent and authorization binding;
- transaction-envelope/calldata binding;
- exact QuickSwap V2 and Uniswap V3 quote primitives with block-bound snapshots;
- shared market-block handling;
- exact sequential cross-venue route composition;
- loan candidate optimizer;
- EVM preflight and simulation-proof binding;
- deterministic Governor and signer boundary;
- durable SQLite nonce/transaction storage;
- atomic execution coordinator;
- private-only submission boundary with no public fallback;
- chain observation and explicit PENDING/INCLUDED/REVERTED/DROPPED/REPLACED/REORGED handling;
- durable recovery observation adapter;
- receipt/settlement reconciliation;
- Phase19 Solidity executor with allowlisted two-leg route topology, replay protection, callback checks, per-leg minimums, strict surplus, and withdrawal isolation;
- Polygon fork protocol smoke and execution-probe harness;
- adversarial/regression test coverage across the above boundaries;
- durable replacement preparation and replacement-fee policy hardening;
- explicit Governor-envelope isolation for replacement preparation in the Phase-19 test harness;
- immutable replacement transaction-record construction;
- atomic durable replacement persistence across transaction and nonce state.

## 4. ROUTE COMMITMENT INTEGRITY

The executable route now has an explicit topology commitment joined with the quote-route commitment. Python and Solidity reference vectors are covered by EVM tests, and mutation tests reject changed route/topology/commitment values.

The cryptographic bridge is still an area for continued hardening: off-chain intent/economic proof, calldata commitment, and on-chain route/topology commitment must remain exactly synchronized without introducing a hash cycle.

## 5. RECOVERY / DURABILITY STATE

Execution lifecycle vocabulary now includes explicit `REORGED`, `REPLACED`, and `DROPPED` states.

Durable recovery records explicit evidence and does not itself sign, submit, create replacements, or release a nonce.

Reorg handling permits canonical re-observation after a durable reorg state.

Startup recovery audit detects inconsistent nonce/transaction mappings and preserves forensic diagnostics.

Replacement preparation is fail-closed on source state, sender/executor identity, nonce linkage, replacement fee policy, EVM preflight, Governor approval, signing, and durable persistence.

Replacement persistence is a dedicated atomic boundary: a validated replacement record is inserted only while the source is explicitly replaceable, the source is moved to `REPLACED`, and the same durable nonce is rebound to the new signed transaction in `SIGNED` state within one SQLite transaction.

## 6. LATEST VERIFIED CI EVIDENCE

Latest completed Phase-19 verification observed:

- Run `#254` on commit `abb5aaa9576dff6f7b9de115107c50a2db8238fe`: **FAIL**
- Solidity compile: PASS
- Phase-19 EVM harness: PASS, 14 tests
- Polygon protocol smoke: PASS, 3 tests
- Polygon fork execution probe: PASS, 1 test
- Python Phase-19 suite: FAIL, **402 tests: 1 failure, 401 passing**
- The remaining failure was the stale expectation that a consumed source would stay `DROPPED`; implementation correctly persisted it as `REPLACED` after replacement installation.

Current verification run:

- Run `#258` on commit `05a9becc1542f6d588cbfc77691beacb8087f29b`: **IN PROGRESS** at checkpoint time.
- This run includes the final replacement-state assertion correction plus the CI trigger isolation change.
- **Status-sync-only commits are now excluded from the Phase-19 push trigger via `paths-ignore: PROJECT_STATUS.md`.** This prevents status recording from creating a self-referential CI loop.
- A status-only commit therefore cannot masquerade as a new implementation verification event.

## 7. CI / STATE-SYNCHRONIZATION CONTROL FIX

The screenshot evidence showed a real mismatch pattern: every `PROJECT_STATUS.md` synchronization created another Phase-19 workflow run because the workflow triggered on every push to the active branch. This produced repeated red runs and moved the branch HEAD even when no production/code behavior changed.

The workflow has now been changed so ordinary Phase-19 verification triggers on implementation changes but ignores `PROJECT_STATUS.md`-only pushes. Manual `workflow_dispatch` remains available for deliberate full verification.

This establishes two distinct truths:

1. **Implementation verification:** tied to an implementation-bearing commit and CI run.
2. **Continuity recording:** may advance the branch with status-only commits without triggering a duplicate verification cycle.

The project must record both explicitly and must never treat a status-only HEAD as fresh test evidence unless the implementation SHA it describes has actually passed CI.

## 8. COMPLETION / DISTANCE ASSESSMENT

These percentages are engineering readiness estimates, not formal certification scores.

- **Core architecture + deterministic implementation:** approximately **75–80% complete**.
- **Go-live evidence/certification:** approximately **45–55% complete**.
- **Overall mission toward first controlled live hunt:** approximately **60–70% complete**.

These are not certification numbers. The project remains in proof/productionization rather than live-execution phase.

## 9. CURRENT BLOCKERS

1. Terminal result for current implementation run `#258` is not yet observed at this checkpoint.
2. After `#258` is green, perform focused adversarial replacement-chain and rollback audit before certifying Phase 19.
3. Continue hardening the route/topology cryptographic bridge and exact execution commitment.
4. Production signer/network credentials remain intentionally absent and locked.
5. Production private relay capability is not yet proven on mainnet.
6. Realized live PnL evidence does not exist.
7. Live mainnet capital deployment remains forbidden.

## 10. GO-LIVE GATES

All must be GREEN with reproducible evidence before live capital:

- exact live-block quote snapshots;
- exact sequential route simulation;
- exact loan-size optimization;
- all-in worst-case economics;
- strict realized `> $0.20`;
- exact EVM preflight;
- secure allowlisted executor;
- proof/hash chain;
- replay protection;
- durable concurrency-safe nonce service;
- production signer;
- private-only relay with no public fallback;
- transaction record/audit trail;
- receipt reconciliation;
- realized PnL proof;
- fork/E2E evidence;
- adversarial/regression evidence;
- startup safety gates.

Any unchecked P0 gate means **LIVE CAPITAL = LOCKED**.

## 11. FIRST LIVE HUNT CRITERIA

The first live hunt is **not date-scheduled**. It becomes eligible only after every P0/go-live gate is GREEN with reproducible evidence and the shadow/staging transition proves the same immutable artifact chain end-to-end.

The first hunt must be a controlled production observation with the same quote block, economic proof, preflight, Governor, signer, private relay, on-chain receipt, settlement reconciliation, and realized-PnL evidence chain used for ordinary execution. Any uncertainty returns the system to BLOCKED.

Therefore no honest calendar date can be certified yet. The earliest possible live hunt is after:

`Phase-19 GREEN → full adversarial certification → production signer + private relay proof → startup safety proof → controlled shadow run → final go-live authorization → first live transaction with minimal capital`

## 12. CONTINUITY RULE

**STRICT EXECUTION RULE:** Every project response must end with a synchronized `PROJECT_STATUS.md` commit. No exceptions.

The synchronized checkpoint must contain:
- current timestamp/checkpoint;
- current phase and atomic task;
- changed files;
- tests/evidence actually observed;
- exact latest implementation commit SHA;
- blockers/risks;
- next action;
- safety boundary.

Append/replace only with evidence-backed state. Never fabricate passes.

## 13. CURRENT CHECKPOINT

**Timestamp:** 2026-09-15T07:57+05:30

**Atomic task:** P19-CI-01 — repair the status/verification feedback loop while closing the last known Phase-19 replacement lifecycle assertion.

**Evidence observed:**
- Screenshots show repeated failures for status synchronization, Governor-boundary isolation, and replacement-persistence checkpoints.
- Run #254 established that all EVM/fork gates passed and only one Python replacement-state assertion remained.
- Current code correction changes that stale assertion to the intended `REPLACED` source state.
- Current workflow correction adds `paths-ignore: PROJECT_STATUS.md`, so status-only commits no longer launch duplicate Phase-19 verification runs.
- Run #258 is currently in progress for the implementation-bearing commit `05a9becc1542f6d588cbfc77691beacb8087f29b`.

**Decision:** wait for terminal #258 evidence. If green, freeze/record Phase-19 replacement lifecycle as verified, run the focused adversarial replacement-chain audit, then advance to the next highest-value unresolved execution-integrity gap. If red, repair only the proven failing layer and rerun.

**Current HEAD:** `05a9becc1542f6d588cbfc77691beacb8087f29b`

**Safety boundary:** No live signing, public broadcast, live capital, or production execution authorization is granted.

**Next atomic action:** observe terminal Run #258 result, then act only on the evidence.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
