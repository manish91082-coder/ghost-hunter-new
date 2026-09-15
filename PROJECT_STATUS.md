# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `6a3bbc63e1c4a99477136a6329e8f34cda0e705c`
- Recovery-settlement repair: `125db946...`
- Fresh recovery-settlement certification run `#420`: **GREEN**
- Production chain observation adapter: `77c3c457...`
- Read-only transaction/receipt RPC allowlist: `64f96d8b...`
- Fresh certification for current chain-observation adapter: **PENDING**
- Certification PR: `#1` OPEN, base `master`
- Live mainnet execution: **BLOCKED**
- Live capital authorization: **BLOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## 1. NON-NEGOTIABLE SAFETY / CONTROL RULES
- Evidence first; contradictory or missing evidence is UNKNOWN/BLOCKED.
- Fail closed on quote, proof, simulation, authorization, nonce, signer, relay, authority, or settlement inconsistency.
- AI cannot override deterministic economics, preflight, governance, authorization, or settlement.
- Private execution has no public fallback.
- Live capital remains locked until every P0 gate has reproducible evidence.
- No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification.
- Private keys and relay authentication material never enter repository code, fixtures, logs, or chat.

## 2. CANONICAL PRODUCTION SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

Initial scope: Polygon, Aave V3, QuickSwap V2, Uniswap V3, USDC/WETH/WMATIC/WBTC, direct two-leg `A → B → A`.

## 3. VERIFIED IMPLEMENTATION CAPABILITIES
Phase 19 contains deterministic economic gating, immutable intent/auth/envelope binding, exact quote and simulation evidence, EVM preflight, Governor, signer verification, durable nonce/transaction state, replacement/recovery, private-only submission, receipt/reconciliation logic, Solidity executor controls, Polygon fork harness, and authority quorum/provenance/freshness controls.

The recovery lifecycle has a durable `SUBMISSION_IN_FLIGHT` barrier, no restoration to retryable `SIGNED`, and a settlement boundary that requires canonical INCLUDED evidence plus a successful receipt before terminal profit accounting.

The high-level private submission boundary remains private-only with no public fallback.

Production chain observation now uses only the existing read-only provider abstraction. It verifies Polygon chain identity, gathers transaction/receipt/pending-nonce evidence, checks canonical block identity for receipts, groups provider observations deterministically, and requires a unique quorum-backed decision before recovered settlement can trust the observation.

The read-only HTTP transport now allowlists `eth_getTransactionByHash` and `eth_getTransactionReceipt` in addition to the existing read methods. Submission/write methods remain blocked before network I/O.

## 4. CI CERTIFICATION PATH
Certified historical gates include signer repair `#349`, signer runbook `#360`, Polygon transport `#364`, production authority assembly `#367`, authority CLI `#371`, provenance `#373/#376`, freshness/reuse `#378/#379/#380`, execution/replacement/signer freshness `#393`, production execution surface `#395`, private-relay repair `#403`, durable-fence certification `#408`, recovery certification `#417`, and recovered-settlement repair certification `#420`.

Run `#418` remains explicit failure evidence for the first recovered-settlement integrity certification attempt. The repair was independently certified by `#420`.

Run `#420` completed successfully across compile, 14/14 EVM integration tests, Polygon fork smoke, Polygon fork execution probe, and the complete Python stage. No GREEN claim is made for the newer chain-observation adapter until its own fresh workflow completes.

## 5. CURRENT SIGNER IDENTITY GATE
The signer exposes a non-secret cryptographic challenge proof. External verification recovers the Ethereum address and requires exact equality with the expected signer address without private-key access.

The mechanism and runbook are CI-certified, but actual production signer identity remains **NOT PROVEN** until controlled externally held evidence is independently verified.

Signer freshness also requires exact executor/signer authority identity and bounded authority freshness before signing.

## 6. CURRENT POLYGON AUTHORITY / PRIVATE RELAY GATES
`phantomx/production_authority.py` consumes only explicit operator-supplied Polygon HTTPS endpoints, quorum, executor address, and expected signer address.

Authority evidence records actual attesting provider names in its canonical digest, and reusable authority evidence requires exact binding plus bounded freshness.

`scripts/observe_production_authority.py` is read-only and emits canonical non-secret authority evidence.

`phantomx/private_submit.py` remains the only high-level raw relay submission boundary. It requires a private relay and rechecks signed-artifact/authority identity immediately before network I/O.

`phantomx/private_relay_http.py` is the dedicated low-level private-relay adapter and `phantomx/production_private_relay.py` is the explicit operator configuration assembly. No real production endpoint or relay credential has been introduced.

`phantomx/production_chain_observation.py` is the new transaction/receipt observation boundary. It has no signer or submission dependency and produces only non-secret quorum evidence.

## 7. CURRENT P0 BLOCKERS
1. Controlled production signer identity proof without exposing private-key material.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like startup/recovery and settlement reorg evidence, including fresh certification of transaction/receipt quorum observation.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. CURRENT CHECKPOINT
Atomic task completed: certify the recovered-settlement repair and introduce a read-only, quorum-bound production transaction/receipt observation boundary for recovery decisions.

Implementation:
- `#420` GREEN certified the recovered-settlement repair.
- `77c3c457...` added deterministic provider consensus for transaction/receipt/pending-nonce evidence.
- `64f96d8b...` expanded the read-only HTTP allowlist only for transaction and receipt observation methods.
- `6a3bbc63...` adds adversarial unit coverage for the new observation adapter.

The new observation adapter is intentionally not connected to production live execution authorization yet. Its fresh full-workflow certification is pending.

## 10. NEXT ATOMIC ACTION
Complete fresh CI certification for `6a3bbc63...`. On GREEN, bind the quorum observation result into durable chain-observation persistence so `SUBMISSION_IN_FLIGHT` recovery can accept only a quorum-backed observation record, while preserving the existing fail-closed lifecycle transitions.

**LIVE SIGNING = BLOCKED**  
**PUBLIC BROADCAST = BLOCKED**  
**LIVE CAPITAL = LOCKED**
