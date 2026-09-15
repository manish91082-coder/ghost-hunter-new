# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. **STRICT RULE: synchronize this file on every assistant project response, without exception.** The synchronization must record the latest known branch HEAD/checkpoint, current phase/task, evidence actually observed, blockers, next action, and safety boundary. Never fabricate passes.

## 0. CURRENT RESUME CARD

- Project: `manish91082-coder/ghost-hunter-new`
- Active implementation branch: `phase-19-e2e-harness`
- Latest implementation-bearing commit: `de6eee477f0e1b8844c88de26be3e884cb8e9d4e` — intent-to-calldata commitment bridge regression hardening
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
- atomic durable replacement persistence across transaction and nonce state;
- CI control that excludes status-only `PROJECT_STATUS.md` commits from verification triggers;
- exact observed-transaction binding for durable recovery;
- recovery semantics that do not manufacture active nonce ownership for an unknown replacement hash;
- repeated replacement-chain testing with restart persistence and stale-source rejection;
- atomic rollback regression for failed replacement persistence;
- intent-to-calldata commitment bridge regression proving that a semantic intent mutation makes the embedded execution commitment stale.

## 4. ROUTE COMMITMENT / CRYPTOGRAPHIC BRIDGE INTEGRITY

The executable route has an explicit topology commitment joined with the quote-route commitment. Python and Solidity reference vectors are covered by EVM tests, and mutation tests reject changed route/topology/commitment values.

The bridge design intentionally excludes `calldata_hash` from the embedded execution commitment to avoid a cryptographic fixed-point cycle, while separately binding the completed calldata hash into the immutable `ExecutionIntent` and transaction envelope.

The latest hardening test mutates an execution-semantic intent field (`deadline`) after calldata generation and verifies that the original embedded execution commitment no longer matches the mutated intent commitment. This closes a regression class where off-chain semantic state could drift while the serialized calldata still carried the earlier commitment.

The remaining certification requirement is end-to-end proof that the same immutable artifact chain remains synchronized across quote route, topology, calldata, economic proof, simulation proof, authorization, and final signed transaction at the signer boundary.

## 5. RECOVERY / DURABILITY STATE

Execution lifecycle vocabulary includes explicit `REORGED`, `REPLACED`, and `DROPPED` states.

Durable recovery records explicit evidence and does not itself sign, submit, create replacements, or release a nonce.

Reorg handling permits canonical re-observation after a durable reorg state.

Startup recovery audit detects inconsistent nonce/transaction mappings and preserves forensic diagnostics.

Replacement preparation is fail-closed on source state, sender/executor identity, nonce linkage, replacement fee policy, EVM preflight, Governor approval, signing, and durable persistence.

Replacement persistence is a dedicated atomic boundary: a validated replacement record is inserted only while the source is explicitly replaceable, the source is moved to `REPLACED`, and the same durable nonce is rebound to the new signed transaction in `SIGNED` state within one SQLite transaction.

Durable recovery lookup is bound to `intent_hash + observed tx_hash`, preventing replacement chains that reuse one intent from resolving to a historical transaction by intent alone.

A chain-observed `REPLACED` event records the observed replacement hash as recovery evidence but does **not** manufacture durable nonce ownership for an unknown transaction. Active nonce ownership advances only through the atomic validated replacement-install boundary.

Repeated replacement preparation preserves the forensic chain `tx0 → tx1 → tx2`, with historical records retained as `REPLACED` and only the newest durably installed transaction owning the nonce in `SIGNED` state before submission.

Failed replacement insertion must roll back source and nonce mutations together. The regression now asserts exact pre-attempt snapshot restoration rather than assuming that the nonce already carries a transaction hash.

## 6. VERIFIED CI EVIDENCE

### Baseline and recovery hardening

- Run `#258` on `05a9becc1542f6d588cbfc77691beacb8087f29b`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **402/402 Python**.
- Run `#261` on `8212bfd315d5aec11521bc40a3302d88f5bbc72c`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **403/403 Python**.
- Run `#262` on `3417387353a0866f50115e873ed5a5353a82fb0c`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **403/403 Python**.
- Run `#266` on `e0f8d4d52118ff9cdeae220038029d1baef2307b`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **404/404 Python**.

### Atomic rollback gate

- Run `#267` on `658ffe0cf686d62897f0551ea0ab9df70e930cdd`: **FAIL** only in the new rollback regression; all EVM/fork gates passed and Python was **404/405**, with the failing assertion expecting a hard-coded nonce tx hash where the fixture had `None` before replacement installation.
- Corrected commit `ed3451f82c4c4934fe1c5bfe23623222a10d3a3b` changed the regression to snapshot exact pre-attempt nonce state and assert exact post-restart equality.
- Run `#268` on `ed3451f82c4c4934fe1c5bfe23623222a10d3a3b`: **PASS / GREEN**. Observed evidence: Solidity compilation PASS, **14/14 EVM**, **3/3 Polygon protocol smoke**, **1/1 Polygon fork execution probe**, and **405/405 Python** tests.

### Current cryptographic bridge hardening

- Commit `de6eee477f0e1b8844c88de26be3e884cb8e9d4e`: added `test_intent_mutation_invalidates_embedded_execution_commitment` to `tests/phase19/test_executor_calldata.py`.
- Run `#269` on `de6eee477f0e1b8844c88de26be3e884cb8e9d4e`: **IN PROGRESS**. No GREEN claim is made yet.

A status-only commit does not trigger the Phase-19 verification workflow because `.github/workflows/phase19-tests.yml` ignores `PROJECT_STATUS.md`-only pushes.

## 7. COMPLETION / DISTANCE ASSESSMENT

These percentages are engineering readiness estimates, not formal certification scores.

- **Core architecture + deterministic implementation:** approximately **75–80% complete**.
- **Go-live evidence/certification:** approximately **50–60% complete**.
- **Overall mission toward first controlled live hunt:** approximately **65–70% complete**.

Phase-19 execution-integrity evidence is materially stronger after the replacement/recovery closure and bridge hardening, but production readiness remains unproven.

## 8. CURRENT BLOCKERS

1. Complete terminal evidence for Run #269.
2. Complete end-to-end cryptographic bridge certification across the immutable execution artifact chain.
3. Prove production signer/network authority under controlled conditions.
4. Prove production private relay capability with no public fallback.
5. Prove startup/recovery operational safety under production-like conditions.
6. Produce controlled shadow/staging evidence using the same immutable artifact chain.
7. Obtain realized live PnL evidence only after all preceding P0 gates are GREEN.
8. Live mainnet capital deployment remains forbidden.

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

**Timestamp:** 2026-09-15T13:05+05:30

**Atomic task:** P19-BRIDGE-01 — final route/topology cryptographic bridge hardening.

**Changed files:**
- `tests/phase19/test_executor_calldata.py` — added semantic intent-mutation regression for the embedded execution commitment.
- `PROJECT_STATUS.md` — synchronized with terminal #268 evidence and current #269 execution state.

**Evidence observed:**
- Run #268 is **GREEN**, proving the corrected replacement rollback regression plus the full existing Phase-19 EVM/Polygon/Python gate set: 14/14 EVM, 3/3 Polygon smoke, 1/1 Polygon fork execution probe, 405/405 Python.
- The new bridge regression is implementation-level and specifically verifies that changing an execution-semantic field after calldata generation produces an execution commitment mismatch against the commitment embedded in the previously generated calldata.
- Run #269 is **IN PROGRESS** against `de6eee477f0e1b8844c88de26be3e884cb8e9d4e`; no result is assumed before terminal evidence.

**Decision:** replacement/recovery hardening is now backed by a green full-gate run. Remain in ACTIVE AUDIT for the new bridge regression until #269 terminates. A green #269 will advance the task to complete signer-boundary bridge certification; a red #269 will trigger a surgical repair based only on observed failure.

**Latest implementation checkpoint:** `de6eee477f0e1b8844c88de26be3e884cb8e9d4e`

**Safety boundary:** No live signing, public broadcast, live capital, or production execution authorization is granted.

**Next atomic action:** observe terminal Run #269 evidence, then perform signer-boundary artifact-chain certification.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
