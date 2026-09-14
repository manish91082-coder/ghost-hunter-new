# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> **Canonical continuity anchor on `master`.** Read this file before continuing PhantomX work in a new chat/session/agent. The detailed Phase-19 implementation checkpoint remains on `phase-19-e2e-harness`; this master copy exists so the project state is discoverable directly from the default branch without merging experimental execution code.

## 0. QUICK RESUME CARD

- **Project:** PhantomX / Flash Loan Ghost Hunter
- **Repository:** `manish91082-coder/ghost-hunter-new`
- **Default branch:** `master`
- **Active implementation branch:** `phase-19-e2e-harness`
- **Latest verified active implementation commit:** `3fad361ee0280f3aeec05e3186060eb3d7b8102d`
- **Current phase:** Phase 19, execution-integrity / E2E policy harness
- **Live mainnet execution:** **BLOCKED**
- **Live capital authorization:** **BLOCKED**
- **Production readiness:** **NOT ACHIEVED**
- **Economic invariant:** realized net profit must be **strictly greater than $0.20 after all applicable costs**
- **Current atomic task:** complete durable/concurrency-safe nonce infrastructure and then integrate TransactionRecord, signer, private relay, EVM preflight, secure executor, receipt reconciliation, and fork/E2E evidence.

## 1. MISSION

Build an autonomous, AI-assisted, deterministic-verifier-controlled Polygon flash-loan arbitrage system that discovers opportunities from real on-chain state, verifies exact economics, performs exact EVM preflight, authorizes an immutable transaction intent, executes atomically through a private path, and independently proves realized net profit after settlement.

**Core rule:** AI proposes/ranks/predicts. Deterministic market data, exact quotes, economic verification, EVM simulation, governance, authorization, and the secure executor decide.

AI must never override deterministic safety or profitability gates.

## 2. SUCCESS DEFINITION

The production chain must be reproducibly proven:

`DISCOVER → LIVE BLOCK SNAPSHOT → DATA/RPC QUORUM → EXACT QUOTES → ROUTE SIMULATION → LOAN OPTIMIZATION → ALL-IN ECONOMICS → WORST-CASE PROFIT GATE → AI RANKING → EVM PREFLIGHT → GOVERNOR → AUTHORIZATION → NONCE → SIGN → PRIVATE SUBMIT → ATOMIC EXECUTE → RECEIPT → SETTLEMENT RECONCILIATION → REALIZED NET PNL`

Canonical realized economics:

`Realized Net PnL = final settlement - flash-loan repayment - DEX fees - price impact/slippage - gas - relay/private execution cost - other applicable costs`

Required:

`Realized Net PnL > $0.20`

Exactly `$0.20` is **FAIL**. A successful receipt is not proof of profit. Expected/forecast PnL is not realized PnL.

## 3. NON-NEGOTIABLE GOVERNANCE

### Evidence-first
- No completion claim without evidence.
- Separate documentation, implementation, unit tests, fork evidence, and production evidence.
- Historical logs are historical context, not current proof.
- Missing evidence means UNKNOWN/BLOCKED, never green by assumption.

### Fail-closed
Missing or inconsistent quote, proof, hash, simulation, authorization, nonce, signer, relay, or settlement evidence means **DO NOT EXECUTE**.

### Change control
Any mutation of route, loan amount, token, venue, fee tier, calldata, gas policy, deadline, nonce, economic proof, simulation proof, or execution configuration invalidates dependent authorization/proofs and requires regeneration.

### AI boundary
AI may discover, rank, forecast, optimize candidates, and detect anomalies. AI may not bypass deterministic profit gates, allowlists, EVM preflight, authorization, or settlement truth.

### Secrets
Never commit private keys, seed phrases, API/RPC credentials, or other secrets. Previously exposed credentials discovered in audit must be rotated/revoked and removed from history as appropriate before production.

### Zero-cost architecture
No mandatory paid infrastructure dependency. Gas and unavoidable execution economics are still real costs and must be modeled.

## 4. AUTO-SAVE / AUTO-FREEZE / AUTO-LOCK

Every meaningful engineering checkpoint must preserve phase, atomic task, changed files, evidence, commit SHA, blockers, risks, safety boundary, and next action.

Execution discipline:

`PRE-AUDIT → IMPLEMENT → UNIT TEST → ADVERSARIAL TEST → REGRESSION TEST → STATIC/INTEGRATION CHECK → EVIDENCE CHECKPOINT → COMMIT → VERIFY → STATUS UPDATE → NEXT`

Freeze the affected path on invariant failure, contradictory evidence, unresolved dependencies, stale quotes/simulation, mutated transaction binding, or incomplete settlement reconciliation.

Remain locked until P0 gates are proven:
- live private-key signing
- live broadcast
- live capital deployment
- production mainnet executor
- public fallback for private execution
- arbitrary/universal calls
- larger loan sizes
- DEX expansion
- AI execution override

## 5. CANONICAL PRODUCTION SPINE

`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

Truth hierarchy:
1. Actual on-chain state
2. Exact quote / deterministic route calculation
3. EVM state simulation
4. Receipt and settlement data
5. Deterministic economic accounting
6. AI forecasts/ranking
7. Historical/documentary claims

## 6. INITIAL PRODUCTION SCOPE

- Chain: Polygon mainnet
- Flash loan: Aave V3
- DEXs: QuickSwap V2, Uniswap V3
- Assets: USDC, WETH, WMATIC, WBTC
- Initial route: direct two-leg `A → B → A`

Triangular and universal arbitrary-call execution remain deferred until the core spine is proven.

## 7. ECONOMIC AND QUOTE TRUTH

Quotes must be bound to a live block/snapshot and must use exact venue semantics. QuickSwap V2 `getAmountsOut` is exact router-output quoting but can become stale. Uniswap V3 must use the actual selected pool and fee tier. V3 liquidity must not be treated as V2 reserves.

Sequential route outputs must feed exactly into the next leg. Price impact, slippage, flash premium, gas, relay cost, and other applicable costs must be included. Aave premium must come from authoritative live protocol state, not a permanent hard-coded assumption. Polygon gas asset is POL and must not be conflated with WMATIC.

## 8. PROOF / HASH CHAIN

`QuoteSnapshot → RoutePlan → EconomicProof → SimulationProof → ExecutionIntent → Authorization → TransactionEnvelope → ReceiptProof → RealizedPnL`

Ethereum integrity hashing uses **Keccak-256**, not NIST SHA3-256.

Conformance vectors:
- Keccak-256(empty) = `c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470`
- Keccak-256(`abc`) = `4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45`

Mutation of an authorized proof/input must fail verification.

## 9. CURRENT PHASE-19 IMPLEMENTATION STATE

Implemented policy/test foundations on `phase-19-e2e-harness` include:

- strict realized-profit policy `net > $0.20`
- explicit all-in cost accounting
- realized settlement model
- execution lifecycle state machine
- immutable `ExecutionIntent`
- Ethereum Keccak-256 hashing boundary
- authorization ↔ intent binding
- authorization ↔ complete transaction-envelope binding
- gas/fee/nonce/sender/executor/chain/calldata binding checks
- one-shot authorization consumption after validation
- adversarial mutation/replay tests
- monotonic nonce reservation model
- nonce ↔ authorization binding
- durable nonce lifecycle reference state machine
- adversarial durable-nonce tests

Important evidence boundary: these are currently **policy/reference/test models**, not yet production signer, durable database-backed concurrency infrastructure, Polygon RPC integration, or live transaction execution.

## 10. CURRENT IMPLEMENTATION FILES

Relevant Phase-19 files include:

```text
phantomx/
├── economics.py
├── execution.py
├── controls.py
├── settlement.py
├── hashing.py
├── authorization.py
├── nonce_manager.py
├── nonce_binding.py
└── durable_nonce.py

tests/phase19/
├── test_invariants.py
├── test_hashing.py
├── test_authorization_controller.py
├── test_nonce_manager.py
├── test_nonce_binding.py
└── test_durable_nonce.py
```

Supporting status artifacts:
- `PHASE19_IMPLEMENTATION_STATUS.md`
- `PHASE19_HASHING_STATUS.md`
- `PHASE19_NONCE_STATUS.md`
- `PHASE19_CURRENT_CHECKPOINT.md` when present on the active implementation line

## 11. LATEST PHASE-19 CHECKPOINT

Latest verified active branch commit:

`3fad361ee0280f3aeec05e3186060eb3d7b8102d`

Commit message:

`Add durable nonce state-machine adversarial tests`

Parent:

`cf7b53d43133411ae29c49e15cc66ce47cd48897`

At this checkpoint:
- durable nonce state machine exists;
- adversarial lifecycle tests exist;
- actual full test execution evidence is still not established;
- production durable storage and cross-process atomicity remain open;
- live signing/broadcast remain locked.

## 12. NEXT EXECUTION PLAN

### P0-A: Durable nonce production boundary
1. Pre-audit current nonce models.
2. Define durable storage contract.
3. Add atomic reservation semantics suitable for multiple workers/processes.
4. Add crash/restart recovery.
5. Reconcile Polygon pending nonce.
6. Track replacement transactions.
7. Handle dropped/reorged transactions.
8. Produce machine-readable nonce audit records.
9. Add adversarial/concurrency/regression tests.
10. Commit and verify evidence.

### P0-B: TransactionRecord
Bind one record across:
`intent → authorization → nonce reservation → built tx → signed tx → relay submission → inclusion → receipt → settlement`

### P0-C: Exact EVM preflight
Prove exact calldata, block/state, gas, route, minOut, repayment, strict surplus, revert behavior, and state-diff expectations before signing.

### P0-D: Secure Solidity executor
Rewrite the current execution skeleton around caller/initiator checks, allowlists, route and proof binding, deadline/freshness, replay protection, execution guard, SafeERC20, strict surplus, and controlled authority.

### P0-E: Signer + private relay
Production signer closure, nonce binding, exact authorization verification, private-only submission, no public fallback, capability verification.

### P0-F: Settlement and realized PnL
Independently reconcile token deltas, repayment, gas, relay cost, and other costs. Only then allow `PROFIT_CONFIRMED`.

### P0-G: Fork/E2E evidence
Run reproducible Polygon fork tests, adversarial tests, regression suite, and controlled end-to-end proof chain.

## 13. GO-LIVE CHECKLIST

All must be GREEN with reproducible evidence before any live capital:

- [ ] exact live-block quote snapshots
- [ ] exact sequential route simulation
- [ ] exact loan-size optimization
- [ ] all-in worst-case economics
- [ ] strict `> $0.20` deterministic gate
- [ ] exact EVM preflight
- [ ] secure allowlisted executor
- [ ] proof/hash chain
- [ ] replay protection
- [ ] durable concurrency-safe nonce service
- [ ] production signer
- [ ] private-only relay with no public fallback
- [ ] transaction record / audit trail
- [ ] receipt reconciliation
- [ ] realized PnL proof
- [ ] fork/E2E evidence
- [ ] adversarial/regression evidence
- [ ] startup safety gates

Until every required gate is green: **LIVE CAPITAL = LOCKED**.

## 14. HISTORICAL CLAIMS WARNING

Historical repository logs may contain claims of completed phases, passing tests, live scans, large scenario counts, oracle records, or training records. Those claims are historical context only and must not be reused as current production proof unless independently reproduced.

The current canonical economic threshold is strict realized net profit `> $0.20` after all applicable costs.

## 15. CONTINUITY / NEW CHAT PROTOCOL

A new chat should begin by reading:

1. `PROJECT_STATUS.md` on `master` for the canonical resume anchor.
2. The latest commit on `phase-19-e2e-harness`.
3. The Phase-19 status/checkpoint files and changed implementation/tests.
4. Actual CI/test/fork evidence where available.

Then reconcile Git against this file before changing code.

Recommended resume instruction:

> Read `PROJECT_STATUS.md` from `manish91082-coder/ghost-hunter-new`, reconcile it with the latest Git state on `phase-19-e2e-harness`, inspect the latest Phase-19 implementation/tests, and continue from the highest-priority unresolved P0 atomic task. Preserve all fail-closed, evidence-first, strict-profit, authorization, nonce, private-relay, and live-capital-lock rules.

## 16. STATUS UPDATE RULE

Every project-execution step that changes state must update the continuity record with:
- timestamp
- phase
- atomic task
- changed files
- tests/evidence actually run
- commit SHA
- blockers
- next action
- safety boundary

Do not fabricate test passes or completion claims. Preserve forensic history.

## FINAL SAFETY STATEMENT

This file is a continuity/governance anchor. It does **not** authorize live execution.

The only acceptable progression is:

`PROVEN DATA → PROVEN ECONOMICS → PROVEN SIMULATION → PROVEN AUTHORIZATION → PROVEN SIGNING → PROVEN PRIVATE EXECUTION → PROVEN RECEIPT → PROVEN REALIZED PROFIT`

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED**

---

### Detailed active-branch status

The full historical Phase-19 continuity document is preserved on `phase-19-e2e-harness` at `/PROJECT_STATUS.md`. It remains the detailed forensic record until a safe, lossless synchronization mechanism is used. The `master` file above is the default-branch canonical resume anchor and intentionally does not merge the experimental Phase-19 implementation into `master`.
