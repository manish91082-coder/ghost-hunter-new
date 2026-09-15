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

- Run `#252` on commit `d21e42183759ed06905c91be98b1e425444dcfc4`: **FAIL**
- Solidity compile: PASS
- Phase-19 EVM harness: PASS, 14 tests
- Polygon protocol smoke: PASS, 3 tests
- Polygon fork execution probe: PASS, 1 test
- Python Phase-19 suite: FAIL

Run `#253`/subsequent intermediate state is not used as certified evidence because no terminal full-suite result has been established here.

Current implementation commits after that evidence:

- `a72ebc2efb61bf742b3a0374657693e72839bd28`: added `TransactionRecord.from_replacement()` with strict source/authorization/identity/nonce/governor/preflight validation.
- `abb5aaa9576dff6f7b9de115107c50a2db8238fe`: added `SQLiteExecutionStore.persist_signed_replacement()` as an atomic source-replace + nonce-rebind + replacement-insert operation.

A new CI run `#254` has been queued for `abb5aaa9576dff6f7b9de115107c50a2db8238fe`. No current-HEAD GREEN claim is made until that workflow reaches a terminal result.

## 7. CURRENT BLOCKERS

1. Obtain terminal CI evidence for the replacement persistence implementation.
2. Add/verify adversarial tests covering replacement record linkage, atomic rollback, and repeated replacement chains if any remain unproven.
3. If the full regression becomes green, perform a focused Phase-19 replacement-lifecycle semantic audit before advancing to the next execution-integrity gap.
4. Continue hardening the route/topology cryptographic bridge and exact execution commitment.
5. Production signer/network credentials remain intentionally absent and locked.
6. Production private relay capability is not yet proven on mainnet.
7. Realized live PnL evidence does not exist.
8. Live mainnet capital deployment remains forbidden.

## 8. GO-LIVE GATES

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

## 9. CONTINUITY RULE

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

## 10. CURRENT CHECKPOINT

**Timestamp:** 2026-09-15T07:26+05:30

**Atomic task:** P19-RC-02 — close the durable replacement-record/storage boundary exposed by CI #249/#252.

**Finding:** The replacement coordinator had advanced beyond the durable record/storage layer. The active code referenced `TransactionRecord.from_replacement()` and `SQLiteExecutionStore.persist_signed_replacement()`, while neither primitive existed in the active branch. CI #252 therefore remained non-green even after the earlier fee-policy corrections.

**Corrective action:**
- `a72ebc2efb61bf742b3a0374657693e72839bd28` implemented immutable replacement-record construction with exact source hash, intent, identity, nonce, authorization, Governor and preflight validation.
- `abb5aaa9576dff6f7b9de115107c50a2db8238fe` implemented atomic replacement persistence: source must be `DROPPED`/`REPLACED`; replacement must be `SIGNED`; source and replacement identity/nonce/reservation must match; current durable nonce must be explicitly replaceable and point to the source hash; replacement record is inserted; source becomes `REPLACED`; nonce becomes `SIGNED` and points to the new replacement hash; all within one SQLite transaction.

**Current HEAD:** `abb5aaa9576dff6f7b9de115107c50a2db8238fe`

**Current CI:** Run `#254` queued for this HEAD; terminal result not yet observed.

**Safety boundary:** No live signing, public broadcast, live capital, or production execution authorization is granted.

**Next atomic action:** verify run `#254`; if any failures remain, repair them at the narrowest correct abstraction layer and rerun full Phase-19 regression. After GREEN, perform focused adversarial replacement-chain audit before advancing.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**