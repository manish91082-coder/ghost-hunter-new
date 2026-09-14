# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> **Canonical continuity document.** Read this file before continuing project execution in a new chat/session/agent. Update it whenever a project execution step changes the state, evidence, architecture, implementation, tests, governance, blockers, or next action.

**Language:** Hindi / Hinglish preferred for operator-facing status.
**Discipline:** Surgical • Military-grade • Aviation-grade • Evidence-first • Fail-closed.
**Document role:** This file is the project state anchor, not a claim that every listed component is production-ready.

---

## 0. QUICK RESUME CARD

**Project:** PhantomX / Flash Loan Ghost Hunter
**Repository:** `manish91082-coder/ghost-hunter-new`
**Default branch:** `master`
**Active implementation line at this checkpoint:** `phase-19-e2e-harness`
**Latest known implementation commit:** `485a3e6aa8e794a4536a47db5385e64b40e1bb4d`
**Current mission phase:** Phase 19, execution-integrity / E2E policy harness
**Live mainnet execution:** **BLOCKED**
**Live capital authorization:** **BLOCKED**
**Production readiness:** **NOT ACHIEVED**
**Strict profit invariant:** realized net profit must be **strictly greater than $0.20 after all applicable costs**
**Current next atomic task:** cryptographically bind authorization to the complete transaction envelope, then harden nonce concurrency and durable authorization semantics before signer/broadcaster integration.

### New-chat resume instruction

1. Read this entire `PROJECT_STATUS.md`.
2. Read the latest Git commit on the active implementation branch.
3. Inspect the files/tests touched by the latest checkpoint.
4. Do not assume historical claims are implementation evidence.
5. Reconcile this status file with Git before executing the next task.
6. Continue from **CURRENT ATOMIC TASK**, not from an older conversation summary.
7. Preserve every hard rule in Sections 3–9.

---

# 1. MISSION

PhantomX / Flash Loan Ghost Hunter ka objective ek **autonomous, AI-assisted, deterministic-verifier-controlled Polygon flash-loan arbitrage system** banana hai jo real on-chain state se opportunities discover kare, exact economics verify kare, exact transaction simulate kare, secure authorization ke baad atomic execution kare, aur receipt ke baad **independent realized wallet/settlement accounting** se prove kare ki trade ne all-in costs ke baad strict positive profit threshold cross kiya.

Core principle:

> **AI proposes/ranks/predicts. Deterministic market data, exact quote engine, economic verifier, EVM simulation, governance and secure executor decide.**

AI ko execution truth define karne ki permission nahi hai.

Long-term system ko continuously learn/evolve karna hai, lekin learning layer kabhi deterministic safety/economic gates ko bypass nahi karegi.

---

# 2. SUCCESS DEFINITION

Project tabhi production-success maana jayega jab reproducible evidence ke saath complete chain prove ho:

`DISCOVER → LIVE BLOCK SNAPSHOT → DATA/RPC QUORUM → EXACT QUOTES → ROUTE SIMULATION → LOAN OPTIMIZATION → ALL-IN ECONOMICS → WORST-CASE PROFIT GATE → AI RANKING → EVM PREFLIGHT → GOVERNOR → AUTHORIZATION → NONCE → SIGN → PRIVATE SUBMIT → ATOMIC EXECUTE → RECEIPT → SETTLEMENT RECONCILIATION → REALIZED NET PNL → LEARNING`

Final economic success:

`Realized Net PnL = final settlement - flash-loan repayment - DEX fees - price impact/slippage costs - gas - relay/private execution cost - other applicable costs`

Required:

`Realized Net PnL > $0.20`

Exactly `$0.20` is **FAIL**, not pass.

A successful blockchain receipt is **not** equivalent to a profitable trade.

A forecasted/expected PnL is **not** realized PnL.

---

# 3. NON-NEGOTIABLE GOVERNANCE RULES

## 3.1 Evidence-first

- No completion claim without evidence.
- Distinguish documentation, implementation, tests, fork evidence, and production evidence.
- Historical logs are historical records, not current proof.
- Never convert a historical assertion into a current fact without verification.
- If evidence is unavailable, mark the gate **UNKNOWN / BLOCKED**, not green.

## 3.2 Fail-closed

When a required dependency, proof, hash, quote, simulation, authorization, signer, nonce, relay capability, or settlement record is missing or inconsistent:

**DO NOT EXECUTE.**

## 3.3 No premature live execution

Until all P0 execution gates are proven, live mainnet execution remains blocked.

## 3.4 AI boundary

AI may:
- discover candidates;
- rank opportunities;
- forecast market behavior;
- suggest route/loan candidates;
- assist anomaly detection;
- assist research and optimization.

AI may not:
- override deterministic profit gates;
- override allowlists;
- bypass EVM preflight;
- bypass authorization;
- change a signed intent silently;
- authorize a trade solely from prediction;
- substitute approximate prices for exact settlement truth.

## 3.5 Change control

Any change to route, loan amount, token, venue, fee tier, calldata, gas policy, deadline, nonce, economic proof, simulation proof, or execution configuration invalidates dependent authorization/proofs and requires regeneration.

## 3.6 Secrets

- Never commit private keys, seed phrases, API credentials, RPC credentials, or other secrets.
- Existing exposed credentials discovered during earlier audit must be rotated/revoked and removed from repository history as appropriate before production use.
- Secrets must not appear in logs or status documents.

## 3.7 Zero-cost architectural constraint

“Zero-cost” means no **mandatory paid** infrastructure dependency. The architecture should remain open-source, self-hostable, serverless/free-tier where practical, and avoid mandatory proprietary SaaS/API/cloud/database/monitoring dependencies.

This does **not** mean gas or unavoidable execution economics are zero. The system must explicitly model real gas and execution costs.

---

# 4. MISSION CONTROL / CONTINUITY PROTOCOL

This file is the persistent project state anchor across chat-thread boundaries.

## 4.1 State model

Every execution checkpoint must preserve:

- mission;
- current phase;
- active atomic task;
- completed tasks;
- blocked tasks;
- changed files;
- commit SHA;
- tests and their actual evidence;
- unresolved risks;
- dependencies;
- safety boundary;
- next action;
- decisions and rationale;
- rollback/recovery information where relevant.

## 4.2 Atomic-task rule

One primary atomic engineering objective at a time.

For each objective:

`PRE-AUDIT → IMPLEMENT → UNIT TEST → ADVERSARIAL TEST → REGRESSION TEST → STATIC/INTEGRATION CHECK → EVIDENCE CHECKPOINT → COMMIT → VERIFY → UPDATE STATUS → NEXT`

Do not silently jump over a failed gate.

## 4.3 Auto-save rule

After every meaningful project execution step, persist the resulting state in Git. This status file must be updated when the step changes project state.

## 4.4 Auto-freeze rule

Freeze the affected execution path when:

- a critical invariant fails;
- evidence contradicts implementation;
- a required dependency is unresolved;
- production security cannot be demonstrated;
- a quote/simulation becomes stale or inconsistent;
- transaction binding is mutated;
- settlement reconciliation is incomplete.

Frozen means **no progression to the dependent live-execution stage** until repaired and re-verified.

## 4.5 Auto-lock rule

The following remain locked until their prerequisites are green:

- live private-key signing;
- live transaction broadcast;
- live capital deployment;
- production mainnet executor;
- public fallback for private execution;
- arbitrary/universal contract calls;
- larger loan sizes;
- DEX expansion;
- AI-driven execution override.

## 4.6 Resume rule

A new chat must not restart the project from memory guesses. It must resume from Git + this file + actual evidence.

---

# 5. CANONICAL ARCHITECTURE

## 5.1 High-level intelligence architecture

`Mission → Global Data Baseline → Canonical Knowledge → Relationship Graph → Live Market Intelligence → Opportunity → Economics → Risk → Simulation → Decision → Controlled Execution → Outcome → Learning → Continuous Evolution`

## 5.2 Production execution spine

`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

## 5.3 Truth hierarchy

1. Actual on-chain state
2. Exact quote / deterministic route calculation
3. EVM state simulation
4. Receipt and settlement data
5. Deterministic economic accounting
6. AI forecasts/ranking
7. Historical/documentary claims

Lower layers never override higher-truth safety gates.

---

# 6. INITIAL PRODUCTION SCOPE

Keep first production scope deliberately narrow:

### Chain
- Polygon mainnet

### Initial venues
- Aave V3 flash loans
- QuickSwap V2
- Uniswap V3

### Initial assets
- USDC
- WETH
- WMATIC
- WBTC

### Initial route class
- Direct two-leg arbitrage:
  `A → B → A`

Triangular and universal arbitrary-call execution are deferred until the core spine is proven.

---

# 7. DATA / QUOTE TRUTH PROTOCOL

## Required canonical objects

### BlockSnapshot
Must bind market observations to:
- chain ID;
- block number;
- block timestamp;
- relevant state context;
- retrieval metadata;
- snapshot hash.

### QuoteSnapshot
Must bind:
- chain ID;
- block number;
- timestamp;
- DEX/venue;
- pool/router;
- token in/out;
- amount in/out;
- fee tier where applicable;
- quoted price;
- price impact where measurable;
- gas estimate/context;
- quote hash.

## Quote rules

- QuickSwap V2 `getAmountsOut` is useful for exact router-output quoting but can become stale before execution.
- Uniswap V3 must use the actual selected pool/fee tier and exact swap semantics, not a generic reserve approximation.
- Spot discovery is not execution truth.
- V3 liquidity cannot be safely treated as simple V2 reserves.
- Sequential route output must propagate exact previous-leg output into the next leg.
- Quote freshness and block binding are mandatory.
- Snapshot mutation requires a new route/economic proof.

---

# 8. ECONOMIC TRUTH / PROFIT PROTOCOL

## 8.1 Canonical threshold

`MIN_REALIZED_NET_PROFIT_USD = 0.20`

`STRICTLY_GREATER = true`

Therefore:

- `$0.199999` → FAIL
- `$0.200000` → FAIL
- `$0.200001` → PASS, subject to every other gate

## 8.2 All-in cost classes

Every economic proof must account for, where applicable:

- flash-loan fee/premium;
- DEX fees;
- price impact;
- slippage/worst-case execution deterioration;
- gas;
- private relay/execution cost;
- other operational/execution costs;
- conservative safety margin.

## 8.3 Aave fee

Do not hard-code a permanent flash-loan premium assumption. The live protocol configuration/governance state must be treated as authoritative.

## 8.4 Gas

Gas must be modeled conservatively and, where practical, calldata/state dependent. Fixed historical gas assumptions are not execution truth.

Polygon's native gas asset is POL; WMATIC is a distinct token and must not be conflated with the gas asset.

## 8.5 Off-chain gate

Candidate must satisfy a conservative worst-case net-profit gate before EVM preflight.

## 8.6 On-chain gate

The executor must enforce a strict surplus invariant. For USDC, `$0.20` equals `200000` raw units, assuming USDC's standard 6-decimal representation, but the actual token decimals must be validated rather than blindly assumed.

The on-chain requirement must be:

`final balance > baseline balance + repayment + required surplus`

where required surplus is derived from the authorized economic policy.

## 8.7 Realized gate

After inclusion, actual settlement must be independently reconciled:

`realized net = actual settlement delta - actual/verified all-in costs`

Only then can `PROFIT_CONFIRMED` be reached.

---

# 9. PROOF / HASH PROTOCOL

Canonical proof chain:

`QuoteSnapshot → RoutePlan → EconomicProof → SimulationProof → ExecutionIntent → Authorization → TransactionEnvelope → ReceiptProof → RealizedPnL`

Hashes bind the objects together.

Ethereum integrity hashing uses **Keccak-256**, not NIST SHA3-256.

Current conformance vectors:

- Keccak-256(empty) = `c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470`
- Keccak-256(`abc`) = `4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45`

SHA-256 is permitted only in explicitly labelled test-only fingerprints and must never silently substitute for Ethereum Keccak.

Any mutation of an authorized proof/input must cause verification failure.

---

# 10. CANONICAL DATA CONTRACTS

The intended package includes:

```text
phantomx/
├── execution/
│   ├── intent.py
│   ├── authorization.py
│   ├── route.py
│   ├── state_machine.py
│   └── hashes.py
├── market/
│   ├── snapshot.py
│   ├── quickswap_v2.py
│   ├── uniswap_v3.py
│   └── aave.py
├── economics/
│   ├── quote_engine.py
│   ├── route_simulator.py
│   ├── loan_optimizer.py
│   ├── cost_engine.py
│   └── pnl.py
├── governance/
│   ├── governor.py
│   ├── risk_limits.py
│   └── circuit_breaker.py
├── signing/
│   ├── nonce_manager.py
│   ├── signer.py
│   └── transaction_builder.py
├── relay/
│   ├── private_relay.py
│   └── capabilities.py
├── settlement/
│   ├── receipt.py
│   ├── reconciler.py
│   └── realized_pnl.py
├── contracts/
│   ├── PhantomXExecutor.sol
│   ├── interfaces/
│   └── libraries/
├── security/
│   ├── allowlists.py
│   ├── validation.py
│   └── kill_switch.py
└── tests/
    ├── unit/
    ├── integration/
    ├── adversarial/
    ├── fork/
    └── e2e/
```

This is the target architecture, not a statement that every module above currently exists or is complete.

---

# 11. EXECUTION INTENT

Current intent model contains:

- `chain_id`
- `executor`
- `sender`
- `loan_asset`
- `loan_amount`
- `route_hash`
- `calldata_hash`
- `economic_proof_hash`
- `simulation_proof_hash`
- `nonce`
- `deadline`
- `minimum_net_profit_usd`

Intent is immutable and deterministically serialized before hashing.

Current implementation uses Ethereum Keccak-256 through `phantomx.hashing`.

---

# 12. AUTHORIZATION PROTOCOL

Authorization must bind at minimum:

- intent hash;
- calldata hash;
- economic proof hash;
- simulation proof hash;
- chain ID;
- executor;
- sender;
- nonce;
- deadline;
- gas limit;
- max fee per gas;
- max priority fee per gas.

Transaction envelope must match authorization exactly on all bound fields.

Authorization consumption must occur only **after complete validation**.

Failed verification must not consume a valid authorization.

Replay must fail.

Current authorization controller is a **test/policy model**, not production durable infrastructure.

---

# 13. EXECUTION LIFECYCLE

Canonical state machine:

`CREATED → SIMULATED → AUTHORIZED → NONCE_RESERVED → BUILT → VERIFIED → SIGNED → PRIVATE_SUBMITTED → PENDING → INCLUDED → RECONCILED → PROFIT_CONFIRMED`

Failure terminal:

`RECONCILED → PROFIT_FAILED`

Invalid skips are forbidden.
Terminal states cannot restart.

---

# 14. NONCE PROTOCOL

Current `NonceBook` is a minimal in-memory test model only.

Production requirements:

- durable nonce state;
- race-safe reservation;
- pending transaction awareness;
- replacement/cancellation handling;
- chain reconciliation;
- restart recovery;
- no duplicate nonce allocation across concurrent workers;
- authorization must bind the reserved nonce;
- stale authorization must not reuse a consumed nonce unintentionally.

Next implementation gate is nonce concurrency and durable production interface design.

---

# 15. PRIVATE EXECUTION PROTOCOL

Private submission is mandatory for production execution.

**No public RPC fallback is permitted for a transaction that is required to remain private.**

Separate roles:

- public/read RPC → market data/read-only;
- simulation RPC → `eth_call`/trace/fork simulation;
- private relay → transaction submission only;
- signer → isolated signing boundary.

Private relay capability must be explicitly detected and proven before authorization.

Failure to obtain private execution capability means **BLOCK**.

Important limitation:

“No gas loss on failed trades” cannot be claimed absolutely. A non-broadcast trade costs no on-chain gas, but an included/reverted transaction can still consume gas unless the chosen private execution mechanism explicitly provides suitable revert protection and that protection is verified.

---

# 16. EVM PREFLIGHT PROTOCOL

Before signing/submission, exact calldata and current state must be simulated.

Preflight must validate:

- chain ID;
- target executor;
- sender;
- nonce;
- calldata;
- route;
- quote freshness;
- minimum outputs;
- deadline;
- flash-loan repayment;
- strict surplus;
- gas estimate/limit;
- fee ceiling;
- expected state/settlement conditions;
- revert reason if failure occurs.

Simulation output must create a `SimulationProof` / `SimulationProofHash` tied to the exact transaction intent.

If any bound input changes, re-simulate and re-authorize.

---

# 17. GOVERNOR / RISK CONTROL

Governor is deterministic and sits above execution.

It must enforce:

- supported chain;
- allowed executor;
- allowed tokens;
- allowed venues;
- allowed route types;
- maximum loan limits;
- minimum profit;
- gas ceiling;
- relay cost ceiling;
- deadline/freshness limits;
- liquidity/risk limits;
- circuit breaker;
- stale data rejection;
- simulation success;
- authorization integrity.

AI cannot override Governor.

Kill switch / pause control must exist before live capital deployment.

---

# 18. SMART-CONTRACT SECURITY TARGET

The current historical `PhantomXMVP.sol` is **not** production-safe and is being treated as a rewrite/reference.

Required production invariants include:

- caller authorization;
- correct Aave pool callback sender;
- correct Aave initiator;
- loan asset allowlist;
- route hash binding;
- token allowlist;
- venue/router allowlist;
- fee-tier binding;
- deadline enforcement;
- quote freshness;
- minimum output enforcement;
- strict repayment + surplus check;
- replay protection;
- execution guard / reentrancy protection;
- safe token transfer/approval semantics;
- bounded rescue authority;
- pause/kill switch;
- no arbitrary universal external call surface in initial production executor;
- deterministic event/audit trail.

The executor must not trust caller-supplied `minOut` or route parameters unless they are cryptographically/economically bound to the authorized proof chain.

---

# 19. CURRENT REPOSITORY HISTORY / BASELINE

Known baseline before Phase 19:

- Default branch: `master`
- Baseline master commit: `594f3763ce651ae5dcdca8a2153bf120b09d5096`
- Latest master documentation commit at that checkpoint: `Add PROJECT_DETAILS.md`
- Earlier major cleanup commit: `9eb1d71302b91a77ac108fc4f00206b48c4d574f`

The repository contains multiple historical architecture generations, including V2 execution work, V3/universal concepts, swarm concepts, and common RPC/guard utilities.

No historical architecture generation should be assumed to be the final production spine without audit and dependency-closure verification.

---

# 20. HISTORICAL COMPONENT STATUS

## V2
Most complete historical execution path and useful implementation reference.

## V3 / Universal Engine
Conceptually broader, but incomplete and not authorized as production execution spine.

## Swarm
Conceptually rich multi-agent architecture, but dependency closure and execution safety must be proven.

## Profitability simulator
Useful for discovery/prototyping, but historically used simplified spread/reserve assumptions. It is not sufficient as final exact route economics.

## Spatial arbitrage scanner
Useful for market discovery/spot signals. It is not final execution truth.

## Historical live runner
Historical dry-run/live-scan claims must not be interpreted as proof of profitable production execution.

---

# 21. PHASE-BY-PHASE PROGRESS

## Phase 0 — Repository / architecture audit
**Status:** Completed as architecture audit.

Identified fragmented generations and selected the deterministic execution spine as the canonical target.

## Phase 1 — Readiness audit
**Status:** Completed.

Approximate readiness at that time was ~32%, with major missing pieces in exact economics, secure executor, signer, private relay, realized accounting, and E2E proof.

## Phase 3 — Economic truth
**Status:** Architecture defined; implementation incomplete.

Identified that AI forecast must remain separate from settlement truth and that exact sequential quote propagation is mandatory.

## Phase 4 — Data / quote integrity
**Status:** Architecture/audit completed; implementation still being built.

Identified V2 `getAmountsOut`, V3 pool/fee-tier issues, stale snapshot risk, simplified triangular math, and inconsistent gas assumptions.

## Phase 5 — Execution lifecycle
**Status:** Architecture defined; implementation incomplete.

Identified missing cryptographic binding, nonce management, private relay purity, signer closure, and realized PnL reconciliation.

## Phase 6 — Protocol
**Status:** Canonical protocol frozen.

Initial scope narrowed to Aave V3 + QuickSwap V2 + Uniswap V3 direct two-leg routes and controlled assets.

## Phase 7 — Contract security
**Status:** Audit complete; rewrite required.

Historical executor is not production-safe.

## Phase 8 — Blueprint
**Status:** Canonical target architecture established.

## Phase 9 — Migration
**Status:** Migration plan established; implementation ongoing.

## Phase 10 — Data contracts
**Status:** Architecture established; implementation partially present in Phase 19 models.

## Phase 11 — Config/security
**Status:** Audit findings established; production remediation required.

Required secret rotation/removal, registry separation, deployment records, dynamic protocol values, and startup safety gates.

## Phase 12 — Market snapshots / exact quote protocol
**Status:** Architecture established; implementation still required in production market adapters.

## Phase 13 — Exact route engine / loan optimizer
**Status:** Architecture established; implementation required.

Target:
`MarketSnapshot → Candidate Routes → Exact Sequential Quotes → Loan Size Search → Price Impact → Flash Fee → Gas → Relay → Worst-Case Net PnL → EconomicProof`

## Phase 14 — Intent / authorization
**Status:** Partially implemented in Phase 19 policy models.

Intent is immutable and hashed with Keccak. Authorization binding is under active hardening.

## Phase 15 — Executor rewrite design
**Status:** Design established; production Solidity rewrite still required.

## Phase 16 — EVM preflight / SimulationProof
**Status:** Design established; production implementation still required.

## Phase 17 / 18 — Integration / readiness architecture
**Status:** Conceptually near-complete; Git implementation remains the bottleneck.

## Phase 19 — Execution-integrity harness
**Status:** **IN PROGRESS**.

Implemented policy/data primitives and adversarial tests. Live execution remains locked.

---

# 22. PHASE 19 IMPLEMENTATION CHECKPOINT

### Implemented

`phantomx/economics.py`
- strict `net > $0.20` policy;
- explicit cost breakdown;
- realized settlement model.

`phantomx/execution.py`
- execution lifecycle vocabulary;
- immutable `ExecutionIntent`;
- Keccak intent hashing;
- `Authorization` binding model;
- `TransactionEnvelope` calldata hashing;
- test-only SHA-256 fingerprints clearly separated.

`phantomx/hashing.py`
- Ethereum Keccak-256 adapter;
- fail-closed behavior if compatible backend unavailable;
- Ethereum Keccak != NIST SHA3 distinction.

`phantomx/controls.py`
- test lifecycle model;
- replay registry;
- minimal nonce book.

`phantomx/settlement.py`
- receipt accounting model;
- actual gas-cost calculation from gas used × effective gas price;
- realized settlement/profit distinction.

`phantomx/authorization.py`
- one-shot authorization controller;
- replay rejection;
- nonce monotonicity policy model;
- expiry/mutation rejection.

### Tests added

- strict profit boundary tests;
- all-cost subtraction;
- successful-but-unprofitable rejection;
- route mutation rejection;
- loan mutation rejection;
- economic proof mutation rejection;
- simulation proof mutation rejection;
- nonce mutation rejection;
- expiry rejection;
- calldata hash mutation;
- lifecycle happy path;
- lifecycle invalid skip;
- terminal-state restart rejection;
- replay tests;
- nonce monotonicity tests;
- receipt success != profit;
- reverted receipt != profit;
- exact gas-cost calculation;
- Keccak conformance vectors;
- authorization replay and mutation tests.

### Evidence boundary

At the latest known checkpoint, the local execution environment could not independently reach GitHub, therefore **no test suite pass / CI success is claimed merely because files were committed**.

This distinction is mandatory.

---

# 23. CURRENT IMPLEMENTATION READINESS

Approximate status at the current checkpoint:

- Architecture/specification: ~98% conceptually defined
- Git production implementation: substantially incomplete
- Full final-goal readiness: roughly 25–30% at the broader project checkpoint
- Phase-19 policy harness: materially implemented, but execution evidence still pending

These percentages are directional project-management indicators, not formal verification metrics.

Do not increase them without evidence.

---

# 24. CURRENT BLOCKERS

1. No independently verified full Phase-19 test-run artifact yet.
2. Production-grade durable nonce manager not implemented.
3. Production signer boundary not completed.
4. Exact transaction builder not completed.
5. Private relay production capability and no-fallback enforcement not completed.
6. Exact production market adapters/quote engine not fully integrated.
7. Exact sequential route simulator not fully integrated.
8. Exact loan optimizer not fully integrated.
9. Production EconomicProof pipeline not fully integrated.
10. EVM SimulationProof pipeline not fully integrated.
11. Production Governor/circuit breaker not fully integrated.
12. Production Solidity executor rewrite not completed.
13. Fork/E2E execution evidence not completed.
14. Receipt-to-wallet realized PnL reconciliation not integrated end-to-end.
15. Secret/config remediation must be completed before production use.
16. Historical executor addresses/configurations require independent on-chain reconciliation before any production authority is assigned.

---

# 25. NEXT EXECUTION PLAN

## Gate A — Authorization ↔ TransactionEnvelope binding

Implement and test a verifier that requires exact match of:

- intent;
- authorization;
- chain ID;
- sender;
- executor;
- nonce;
- calldata Keccak;
- gas limit;
- max fee;
- priority fee;
- deadline.

Verification failure must not consume authorization.

## Gate B — Nonce concurrency

Implement adversarial tests for concurrent reservation semantics and define the production durable interface.

## Gate C — Transaction record

Create immutable transaction record containing:

- intent hash;
- authorization hash;
- nonce;
- calldata hash;
- transaction envelope hash;
- signing metadata;
- relay submission metadata;
- receipt metadata;
- reconciliation status.

## Gate D — Exact EVM preflight

Build the real `SimulationProof` pipeline.

## Gate E — Production signer / builder

Only after A–D are proven.

## Gate F — Private relay

No public fallback. Capability must be explicit and testable.

## Gate G — Solidity executor rewrite

Implement secure allowlisted executor and strict on-chain surplus invariant.

## Gate H — Polygon fork E2E

Test exact Aave + QuickSwap + Uniswap V3 execution semantics against realistic state.

## Gate I — Shadow mode

Run discovery/economics/simulation without live capital. Collect reproducible evidence.

## Gate J — Controlled live pilot

Only after every P0 gate is green, with tiny bounded exposure and automatic kill switch.

---

# 26. P0 GO-LIVE GATE CHECKLIST

All must be GREEN:

- [ ] exact block/snapshot integrity
- [ ] exact QuickSwap V2 quote adapter
- [ ] exact Uniswap V3 quote adapter
- [ ] dynamic Aave flash-loan premium
- [ ] exact sequential route simulation
- [ ] conservative loan optimizer
- [ ] all-in economic accounting
- [ ] strict realized net > $0.20
- [ ] exact EVM preflight
- [ ] SimulationProof hash
- [ ] immutable ExecutionIntent
- [ ] Authorization binding
- [ ] transaction envelope binding
- [ ] replay protection
- [ ] durable race-safe nonce manager
- [ ] production signer boundary
- [ ] transaction builder
- [ ] private relay capability
- [ ] no public fallback
- [ ] secure Solidity executor
- [ ] allowlists
- [ ] deadline/freshness controls
- [ ] pause/kill switch
- [ ] receipt proof
- [ ] actual gas accounting
- [ ] realized settlement reconciliation
- [ ] realized wallet PnL
- [ ] adversarial suite
- [ ] regression suite
- [ ] Polygon fork suite
- [ ] E2E proof chain
- [ ] reproducible CI/test evidence
- [ ] secrets/config remediation
- [ ] deployment/bytecode/source verification

**Any unchecked P0 item = LIVE EXECUTION BLOCKED.**

---

# 27. EVIDENCE LEVELS

### E0 — Documentation
Architecture, plans, claims, diagrams.

### E1 — Automated tests
Unit/adversarial/regression tests actually executed.

### E2 — Fork / real-chain simulation
Realistic state and transaction behavior reproduced.

### E3 — Reproducible production transaction
Actual transaction + receipt + settlement + independent PnL proof.

Do not describe E0 as E1, E1 as E2, or E2 as E3.

---

# 28. TESTING DOCTRINE

Required layers:

1. Unit
2. Property/invariant
3. Adversarial
4. Regression
5. Integration
6. Fork
7. E2E
8. Shadow production
9. Controlled production

Failure handling:

`FAIL → FREEZE → FORENSIC REVIEW → PATCH → REGRESSION → RE-RUN → EVIDENCE → UNFREEZE`

No “looks fine” acceptance.

---

# 29. FORENSIC AUDIT PROTOCOL

When a failure appears:

1. Freeze dependent path.
2. Capture exact error/evidence.
3. Identify first violated invariant.
4. Identify whether defect is data, economics, state, authorization, nonce, signing, relay, contract, or settlement.
5. Patch the smallest safe boundary.
6. Add a regression test that would have caught it.
7. Re-run all affected tests.
8. Verify Git diff.
9. Commit with descriptive message.
10. Update this status file.
11. Only then continue.

---

# 30. ROLLBACK / RECOVERY RULE

Every production-affecting change must have a known rollback strategy.

Never force-rewrite history to hide failed experiments.

Prefer additive, reviewable commits.

A broken branch may be abandoned/frozen while preserving evidence. Do not delete forensic history merely to make status appear clean.

---

# 31. DECISION LOG

### Decision D-001
AI is advisory/ranking only. Deterministic verifier is the execution authority.

### Decision D-002
Initial production route scope is direct two-leg `A → B → A`.

### Decision D-003
Initial venues are Aave V3, QuickSwap V2, Uniswap V3.

### Decision D-004
Initial asset set is USDC, WETH, WMATIC, WBTC.

### Decision D-005
Strict realized profit requirement is `> $0.20` after all applicable costs.

### Decision D-006
Private execution is required; public fallback is forbidden.

### Decision D-007
Ethereum Keccak-256 is the canonical integrity hash.

### Decision D-008
Historical V2/V3/swarm code is reference material until independently verified.

### Decision D-009
Production Solidity executor must be rewritten around allowlists, route/proof binding, strict surplus, replay protection, and controlled authority.

### Decision D-010
No live mainnet capital until P0 checklist is completely green with evidence.

---

# 32. HISTORICAL CLAIMS THAT MUST NOT BE REUSED AS CURRENT PROOF

The repository's historical conversation log contains claims such as completed MVP phases, passing tests, live scans, large scenario counts, oracle records, and training records. These are retained as historical context only.

They must not be cited as current production proof unless the underlying artifact/test/transaction is independently reproduced and verified.

The historical default profit threshold also conflicts with the canonical current threshold in this file. **Current canonical threshold wins: strict realized net > $0.20 after all costs.**

---

# 33. CHAT / THREAD CONTINUITY PROTOCOL

If the conversation thread ends:

**Do not restart from scratch.**

New chat prompt can simply say:

> “Read `PROJECT_STATUS.md` from `manish91082-coder/ghost-hunter-new`, reconcile it with the latest Git state, and continue from CURRENT ATOMIC TASK under the same governance rules.”

The next agent must:

- read the file;
- verify the referenced branch/commit;
- inspect actual changed files;
- verify evidence;
- continue from the recorded state.

If Git state and this file disagree, **Git/evidence must be reconciled before execution continues**. Do not silently choose whichever looks convenient.

---

# 34. STATUS UPDATE PROTOCOL

Every project-execution response that changes state must update this file with:

- timestamp/date;
- phase;
- atomic task;
- what changed;
- files changed;
- tests/evidence;
- commit SHA;
- blockers;
- next action;
- safety boundary.

Append a checkpoint rather than erasing forensic history.

If no project state changed, do not fabricate a checkpoint merely to create activity.

---

# 35. CURRENT CHECKPOINT LOG

## Checkpoint 2026-09-14 — Phase 19 continuity anchor

**Atomic task:** Create a permanent project continuity/status document so work survives chat-thread boundaries.

**Action:** This `PROJECT_STATUS.md` document is being established as the canonical project-state anchor, containing mission, architecture, economics, governance, continuity, safety locks, evidence rules, current implementation status, blockers, and next execution plan.

**Source state reconciled:** latest known Phase-19 implementation commit `485a3e6aa8e794a4536a47db5385e64b40e1bb4d` on `phase-19-e2e-harness`.

**Live execution:** BLOCKED.

**Test evidence:** No new pass claim made by this checkpoint. Existing Phase-19 status explicitly states that prior local execution could not independently verify the committed suite.

**Next atomic task after continuity checkpoint:** Authorization ↔ TransactionEnvelope exact binding verification, followed by nonce concurrency/durable nonce infrastructure.

---

# 36. OPERATOR COMMANDS

### `Next`
Continue the highest-priority unresolved atomic task from this file after a fresh pre-audit.

### `Status`
Reconcile this file with Git and report current evidence-backed state.

### `Audit`
Perform forensic audit of current phase before changing code.

### `Freeze`
Stop progression of the affected execution path and record blocker/evidence.

### `Resume`
Only resume a frozen path after its prerequisite evidence is repaired and verified.

### `Verify`
Check implementation, tests, Git diff/commit, and evidence without advancing scope unnecessarily.

---

# 37. FINAL SAFETY STATEMENT

This document is a continuity and governance control plane. It does **not** itself authorize live execution.

**No amount of documentation, AI confidence, historical success, or expected profit can bypass the deterministic P0 gates.**

The only acceptable production progression is:

`PROVEN DATA → PROVEN ECONOMICS → PROVEN SIMULATION → PROVEN AUTHORIZATION → PROVEN SIGNING → PROVEN PRIVATE EXECUTION → PROVEN RECEIPT → PROVEN REALIZED PROFIT`

Until that chain is reproducibly demonstrated, PhantomX remains in controlled engineering/shadow state.

**MISSION STATUS: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED**
