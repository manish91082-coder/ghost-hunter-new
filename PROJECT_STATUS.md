# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. **STRICT RULE: synchronize this file on every assistant project response, without exception.** The synchronization must record the latest known branch HEAD/checkpoint, current phase/task, evidence actually observed, blockers, next action, and safety boundary. Never fabricate passes.

## 0. CURRENT RESUME CARD

- Project: PhantomX / Flash Loan Ghost Hunter
- Repository: `manish91082-coder/ghost-hunter-new`
- Default branch: `master`
- Active implementation branch: `phase-19-e2e-harness`
- Current branch HEAD: `abb5aaa9576dff6f7b9de115107c50a2db8238fe`
- Current HEAD commit: `fix(P19-RC-02): implement atomic replacement persistence boundary`
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

Latest completed Phase-19 verification observed before this checkpoint:

- Run `#254` on commit `abb5aaa9576dff6f7b9de115107c50a2db8238fe`: **FAIL**
- Solidity compile: PASS
- Phase-19 EVM harness: PASS, 14 tests
- Polygon protocol smoke: PASS, 3 tests
- Polygon fork execution probe: PASS, 1 test
- Python Phase-19 suite: FAIL, **402 tests: 1 failure, 401 passing**

Forensic result from run #254:

- All major EVM/fork gates passed.
- Four replacement-coordinator tests passed, including the Governor ceiling boundary and private-submission path.
- The only remaining failure is an assertion in `test_drop_state_is_consumed_into_new_signed_replacement`: after a successful replacement installation, the source transaction is correctly persisted as `REPLACED`, while the test still expected it to remain `DROPPED`.
- This indicates the implementation and test semantics are now one lifecycle transition apart, not an unresolved fee/persistence API error.

## 7. COMPLETION / DISTANCE ASSESSMENT

These percentages are engineering readiness estimates, not formal certification scores.

- **Core architecture + deterministic implementation:** approximately **75–80% complete**.
- **Go-live evidence/certification:** approximately **45–55% complete**.
- **Overall mission toward first controlled live hunt:** approximately **60–70% complete**.

The remaining work is concentrated in proof and productionization rather than basic architecture. The current Phase-19 blocker is one semantic test expectation; after that, the project still requires a focused replacement-lifecycle adversarial audit, route/topology commitment hardening, production signer/network validation, private-relay validation, startup safety validation, and a controlled non-capital / shadow-to-live transition with reproducible evidence.

## 8. CURRENT BLOCKERS

1. Close the single remaining Phase-19 replacement lifecycle test failure and rerun the full 402-test suite.
2. Perform focused adversarial replacement-chain and rollback audit before certifying Phase 19.
3. Continue hardening the route/topology cryptographic bridge and exact execution commitment.
4. Production signer/network credentials remain intentionally absent and locked.
5. Production private relay capability is not yet proven on mainnet.
6. Realized live PnL evidence does not exist.
7. Live mainnet capital deployment remains forbidden.

## 9. GO-LIVE GATES

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

## 10. FIRST LIVE HUNT CRITERIA

The first live hunt is **not date-scheduled**. It becomes eligible only after every P0/go-live gate is GREEN with reproducible evidence and the shadow/staging transition proves the same immutable artifact chain end-to-end.

The first hunt must be a controlled production observation with the same quote block, economic proof, preflight, Governor, signer, private relay, on-chain receipt, settlement reconciliation, and realized-PnL evidence chain used for ordinary execution. Any uncertainty returns the system to BLOCKED.

Therefore no honest calendar date can be certified yet. The earliest possible live hunt is after:

`Phase-19 GREEN → full adversarial certification → production signer + private relay proof → startup safety proof → controlled shadow run → final go-live authorization → first live transaction with minimal capital`

## 11. CONTINUITY RULE

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

## 12. CURRENT CHECKPOINT

**Timestamp:** 2026-09-15T07:35+05:30

**Atomic task:** P19-RC-03 — close the final replacement-lifecycle semantic mismatch exposed by CI #254.

**Finding:** CI #254 verifies that the durable replacement persistence implementation is functioning through all four replacement coordinator lifecycle tests except for one stale assertion. The implementation changes a successfully consumed `DROPPED` source into `REPLACED`, while the test expected the old `DROPPED` state after replacement installation.

**Decision:** Correct the test expectation to the intended durable lifecycle (`source = REPLACED`, replacement = SIGNED, nonce = SIGNED on the new tx), then rerun the complete Phase-19 suite. Do not weaken lifecycle transitions.

**Current HEAD:** `abb5aaa9576dff6f7b9de115107c50a2db8238fe`

**Latest CI:** Run #254 failed only on the stale source-state assertion described above.

**Safety boundary:** No live signing, public broadcast, live capital, or production execution authorization is granted.

**Next atomic action:** update the single stale lifecycle assertion, rerun full Phase-19 verification, then perform adversarial replacement-chain audit if green.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
