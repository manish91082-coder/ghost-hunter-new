# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. **STRICT RULE: synchronize this file on every assistant project response, without exception.** The synchronization must record the latest known branch HEAD/checkpoint, current phase/task, evidence actually observed, blockers, next action, and safety boundary. Never fabricate passes.

## 0. CURRENT RESUME CARD

- Project: `manish91082-coder/ghost-hunter-new`
- Active implementation branch: `phase-19-e2e-harness`
- Latest implementation-bearing commit: `2cf90abcf8e613f09fefaa7ab35c4262be53e779` — signed artifact exact-envelope certification regression
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
- intent-to-calldata commitment bridge regression proving that a semantic intent mutation makes the embedded execution commitment stale;
- signer-boundary regression proving the final type-2 signed artifact exactly carries the governed chain, nonce, gas, executor, zero value, calldata, and empty access-list fields.

## 4. ROUTE COMMITMENT / CRYPTOGRAPHIC BRIDGE INTEGRITY

The executable route has an explicit topology commitment joined with the quote-route commitment. Python and Solidity reference vectors are covered by EVM tests, and mutation tests reject changed route/topology/commitment values.

The bridge design intentionally excludes `calldata_hash` from the embedded execution commitment to avoid a cryptographic fixed-point cycle, while separately binding the completed calldata hash into the immutable `ExecutionIntent` and transaction envelope.

Semantic mutation after calldata generation is now covered, and the signer boundary separately proves that the serialized transaction bytes exactly preserve the governed envelope fields.

The remaining certification requirement is to prove the complete immutable artifact chain in one coherent signer-boundary test path: quote route → topology → calldata → economic proof → simulation proof → execution intent → authorization → Governor decision → executor authority → signed transaction hash/raw bytes. No live submission is required for this certification.

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

Failed replacement insertion rolls back source and nonce mutations together, with regression coverage for exact pre-attempt snapshot restoration.

## 6. VERIFIED CI EVIDENCE

### Baseline and recovery hardening

- Run `#258` on `05a9becc1542f6d588cbfc77691beacb8087f29b`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **402/402 Python**.
- Run `#261` on `8212bfd315d5aec11521bc40a3302d88f5bbc72c`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **403/403 Python**.
- Run `#262` on `3417387353a0866f50115e873ed5a5353a82fb0c`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **403/403 Python**.
- Run `#266` on `e0f8d4d52118ff9cdeae220038029d1baef2307b`: **PASS / GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **404/404 Python**.

### Atomic rollback gate

- Run `#267` on `658ffe0cf686d62897f0551ea0ab9df70e930cdd`: **FAIL** only in the new rollback regression because the test assumed a pre-existing nonce tx hash that the fixture correctly had as `None`.
- Corrected commit `ed3451f82c4c4934fe1c5bfe23623222a10d3a3b` changed the regression to snapshot exact pre-attempt durable nonce state and assert exact post-restart restoration.
- Run `#268` on `ed3451f82c4c4934fe1c5bfe23623222a10d3a3b`: **PASS / GREEN**, Solidity compile PASS, **14/14 EVM**, **3/3 Polygon protocol smoke**, **1/1 Polygon fork execution probe**, **405/405 Python**.

### Cryptographic bridge hardening

- Commit `de6eee477f0e1b8844c88de26be3e884cb8e9d4e`: added semantic intent-mutation regression for the embedded execution commitment.
- Run `#269` on `de6eee477f0e1b8844c88de26be3e884cb8e9d4e`: **PASS / GREEN**, Solidity compile PASS, **14/14 EVM**, **3/3 Polygon protocol smoke**, **1/1 Polygon fork execution probe**, **406/406 Python**. The new `test_intent_mutation_invalidates_embedded_execution_commitment` passed.

### Signer-boundary certification step

- Commit `2cf90abcf8e613f09fefaa7ab35c4262be53e779`: added `test_signed_artifact_exactly_matches_governed_envelope` to `tests/phase19/test_signer.py`.
- The new test decodes the exact serialized EIP-1559 artifact and verifies chain id, nonce, fee fields, gas limit, executor, zero value, calldata, access-list, and transaction hash against the governed envelope/artifact.
- A new CI run is expected from this implementation-bearing push; no result is claimed until terminal evidence is observed.

A status-only commit does not trigger the Phase-19 verification workflow because `.github/workflows/phase19-tests.yml` ignores `PROJECT_STATUS.md`-only pushes.

## 7. COMPLETION / DISTANCE ASSESSMENT

These percentages are engineering readiness estimates, not formal certification scores.

- **Core architecture + deterministic implementation:** approximately **75–80% complete**.
- **Go-live evidence/certification:** approximately **50–60% complete**.
- **Overall mission toward first controlled live hunt:** approximately **65–70% complete**.

These remain engineering readiness estimates, not formal certification scores.

## 8. CURRENT BLOCKERS

1. Terminal evidence for the new signer-boundary CI run.
2. Complete single-path immutable artifact-chain certification at the signer boundary.
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

**Timestamp:** 2026-09-15T13:30+05:30

**Atomic task:** P19-SIGN-01 — signer-boundary artifact certification.

**Changed files:**
- `tests/phase19/test_signer.py` — added exact signed-artifact-to-governed-envelope regression.
- `PROJECT_STATUS.md` — synchronized after observing #269 GREEN.

**Evidence observed:**
- Run #269 is **GREEN**, closing the previous bridge regression checkpoint with the full Phase-19 gate set: 14/14 EVM, 3/3 Polygon smoke, 1/1 Polygon fork execution probe, 406/406 Python.
- Existing signer suite already proves authorization, Governor, executor authority, signer identity, recovered sender, and pre-sign mutation rejection; the new regression adds byte-level verification of the final EIP-1559 transaction against the governed envelope.
- No new CI result exists yet for commit `2cf90abcf8e613f09fefaa7ab35c4262be53e779` at this checkpoint, so this signer-boundary step remains unverified by the full workflow.

**Decision:** continue in ACTIVE AUDIT. Do not treat the new signer-boundary test as certified until its own full CI run terminates green. Once green, use the combined evidence to close the off-chain-to-signed-artifact bridge audit and move to controlled production signer/network authority proof.

**Latest implementation checkpoint:** `2cf90abcf8e613f09fefaa7ab35c4262be53e779`

**Safety boundary:** No live signing, public broadcast, live capital, or production execution authorization is granted. The new test performs only deterministic local serialization/recovery checks.

**Next atomic action:** observe terminal CI evidence for the signer-boundary implementation checkpoint.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
