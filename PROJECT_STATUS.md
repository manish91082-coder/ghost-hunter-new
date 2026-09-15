# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. **STRICT RULE: synchronize this file on every assistant project response, without exception.** The synchronization must record the latest known branch HEAD/checkpoint, current phase/task, evidence actually observed, blockers, next action, and safety boundary. Never fabricate passes.

## 0. CURRENT RESUME CARD

- Project: PhantomX / Flash Loan Ghost Hunter
- Repository: `manish91082-coder/ghost-hunter-new`
- Default branch: `master`
- Active implementation branch: `phase-19-e2e-harness`
- Current branch HEAD (latest implementation-bearing checkpoint): `3417387353a0866f50115e873ed5a5353a82fb0c`
- Latest implementation commit: `test(P19-RA-01): verify replacement nonce ownership follows chain`
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
- durable nonce active-hash advancement when a replacement is observed.

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

Durable recovery lookup is bound to `intent_hash + observed tx_hash`, preventing replacement chains that reuse one intent from resolving to a historical transaction by intent alone.

For an observed `REPLACED` event, the durable nonce now advances its active `tx_hash` to the replacement transaction and records the replaced hash in `replacement_of`, preserving one authoritative active transaction per nonce.

## 6. VERIFIED CI EVIDENCE

### Implementation-bearing GREEN gate

- Run `#258` on commit `05a9becc1542f6d588cbfc77691beacb8087f29b`: **PASS / GREEN**
- Solidity compile: PASS
- Phase-19 EVM harness: PASS, 14 tests
- Polygon protocol smoke: PASS, 3 tests
- Polygon fork execution probe: PASS, 1 test
- Python Phase-19 suite: PASS, **402/402**

Run #258 is the authoritative completed GREEN proof for the pre-audit implementation state. It executed commit `05a9...`, not a status-only commit.

### Post-GREEN adversarial audit in progress

- Run `#261` on `8212bfd315d5aec11521bc40a3302d88f5bbc72c`: **IN PROGRESS** at checkpoint time.
- `8212...` fixes durable recovery lookup to bind the exact observed transaction hash and updates the active durable nonce hash when a replacement is observed.
- Run `#262` on `3417387353a0866f50115e873ed5a5353a82fb0c`: **QUEUED** at checkpoint time.
- `341738...` adds the regression test proving a reused execution intent cannot cause recovery evidence for a replacement transaction to resolve against the historical source record.

A status-only commit does not trigger the Phase-19 verification workflow because `.github/workflows/phase19-tests.yml` ignores `PROJECT_STATUS.md`-only pushes.

## 7. COMPLETION / DISTANCE ASSESSMENT

These percentages are engineering readiness estimates, not formal certification scores.

- **Core architecture + deterministic implementation:** approximately **75–80% complete**.
- **Go-live evidence/certification:** approximately **45–55% complete**.
- **Overall mission toward first controlled live hunt:** approximately **60–70% complete**.

The completed Phase-19 CI gate moves execution-integrity proof forward materially, but it does not establish production readiness or authorize live capital.

## 8. CURRENT BLOCKERS

1. Complete and pass the post-GREEN replacement recovery adversarial audit, including repeated replacement-chain semantics and rollback behavior.
2. Establish final route/topology cryptographic bridge certification.
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

**Timestamp:** 2026-09-15T08:02+05:30

**Atomic task:** P19-RA-01 — adversarial certification of replacement/recovery-chain integrity after Phase-19 GREEN.

**Finding:** Run #258 is a genuine GREEN implementation-bearing verification with 402/402 Python tests and all EVM/fork gates passing. Post-GREEN forensic audit then found two linked recovery-integrity weaknesses: recovery lookup was ambiguous when multiple transaction records shared one intent, and observed replacement evidence could update nonce lifecycle state without advancing the nonce's active transaction hash.

**Corrective action:**
- `8212bfd315d5aec11521bc40a3302d88f5bbc72c` binds durable recovery lookup to the exact observed transaction hash and advances the active nonce hash on `REPLACED` evidence.
- `3417387353a0866f50115e873ed5a5353a82fb0c` adds a targeted regression test for reused-intent replacement-record selection and nonce ownership continuity.

**Current implementation checkpoint:** `3417387353a0866f50115e873ed5a5353a82fb0c`

**Current CI:** Run #261 is in progress for `8212...`; Run #262 is queued for `341738...`. No post-audit GREEN claim is made until the implementation-bearing #262 terminal evidence is observed.

**Safety boundary:** No live signing, public broadcast, live capital, or production execution authorization is granted.

**Next atomic action:** observe #261/#262 terminal evidence; if green, extend the replacement audit to multi-step replacement/recovery chains and atomic rollback, then certify the Phase-19 execution-integrity gate before moving to the next highest-value unresolved P0 gap.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
