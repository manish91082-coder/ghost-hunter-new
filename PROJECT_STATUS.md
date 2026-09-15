# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `125db946bfc2c8e6c3b98910e733818df46a22b4`
- Recovered-settlement integrity repair: `125db946...`
- Private-relay HTTP transport: `b7789d8da6c1eea70cc86e0ee5dd04dac3895694`
- Relay secrecy/fallback-audit repair: `a1f76fcda0ff066b43a2dc0f19e08d682e98657b`
- Durable submission fence: `4c748c058ae32af3074232bfc282dce0e5a71f84`
- Fresh durable-fence certification run `#408`: **GREEN** for `0b1acae...`
- In-flight observation integration: `ebb9d2cb95fa2f43176547daa5520f575fb24ead`
- In-flight durable recovery integration: `4bf326ec13e08dbcf90567b9c5758b4cb6812499`
- In-flight restart-audit hardening: `978047b57e19a802a14593bc9bb683106ee0c419`
- In-flight signed-nonce observation repair: `4376a4692b07d1191d63ab3f13836417326a3252`
- Fresh recovery certification run `#417`: **GREEN** for `e18e060...`
- Recovered-settlement integrity regression tests: `080ffd5ac1093a2189fa60517900a6940b22363a`
- Fresh certification run `#418`: **FAILED** on settlement-test observation-shape mismatch
- Repair commit for #418: `125db946...`
- Fresh repair certification run `#420`: **IN PROGRESS** for `125db946...`
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

The high-level private submission boundary accepts governed immutable signed artifacts, revalidates executor authority before network I/O, requires an explicitly private relay, and has no public fallback.

The Polygon read transport remains read-only; write/submission methods are blocked before network I/O.

The dedicated private-relay transport accepts only non-empty raw signed transaction bytes, sends only `eth_sendRawTransaction`, requires HTTPS and explicit private assertion, separates authentication from endpoint configuration, and validates the returned transaction hash.

The durable submission path establishes a committed `SUBMISSION_IN_FLIGHT` barrier immediately before network I/O. An uncertain relay outcome is never returned to retryable `SIGNED`; the exact durable transaction hash remains held for chain reconciliation.

Chain observation accepts `SUBMISSION_IN_FLIGHT`. When the transaction is in-flight and its nonce record is still legitimately SIGNED/hash-free, explicit PENDING/INCLUDED/REVERTED evidence advances the nonce to the corresponding post-network lifecycle. No observation path restores `SIGNED` after the in-flight fence.

Dedicated recovery accepts `DROPPED`, `REPLACED`, and `REORGED` evidence from applicable in-flight/submitted lifecycle states without reopening `SIGNED`. Direct reorg recovery requires a prior canonical inclusion identity rather than manufacturing a reorg from an unconfirmed relay outcome.

Startup recovery audit treats `SUBMISSION_IN_FLIGHT` with a SIGNED/hash-free nonce lifecycle as internally consistent, preserving the crash-safe fence across process restart.

The settlement boundary requires canonical INCLUDED evidence plus a successful receipt before terminal profit accounting. Recovery states do not directly create settlement authority, and the existing realized-profit floor remains strictly greater than $0.20 after all applicable costs.

## 4. CI CERTIFICATION PATH
Certified historical gates include signer repair `#349`, signer runbook `#360`, Polygon transport `#364`, production authority assembly `#367`, authority CLI `#371`, provenance `#373/#376`, freshness/reuse `#378/#379/#380`, execution/replacement/signer freshness `#393`, production execution surface `#395`, private-relay repair `#403`, durable-fence certification `#408`, and recovery certification `#417`.

Run `#406` remains explicit failure evidence for pre-migration relay-state assertions. Run `#414` remains explicit failure evidence for the first signed-nonce handoff implementation. Both failures led to targeted contract repairs rather than being suppressed.

Run `#417` completed GREEN across the full workflow. Compile, 14/14 EVM integration tests, Polygon fork smoke, Polygon fork execution probe, and the Python unittest stage all completed successfully for the corrected recovery test tree.

Run `#418` is explicit failure evidence for the first recovered-settlement integrity certification attempt. Its failure was confined to the adversarial settlement tests passing the persisted observation wrapper where reconciliation requires the contained canonical `ObservationDecision`.

Repair `#420` is now running against `125db946...`. No GREEN claim is made until the run completes successfully.

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

Current implementation certification remains separate from proof of an approved or connected production relay.

## 7. CURRENT P0 BLOCKERS
1. Controlled production signer identity proof without exposing private-key material.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like startup/recovery and settlement reorg evidence, including certification of `SUBMISSION_IN_FLIGHT` resolution and recovered settlement-integrity controls.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. CURRENT CHECKPOINT
Atomic task: repair the #418 settlement-integrity certification failure caused by persisted-observation wrapper/decision mismatch.

Implementation:
- `125db946...` normalizes `PersistedObservation.observation` before calling settlement reconciliation.
- The reorg test now reuses the original persisted inclusion evidence as stale evidence after the durable lifecycle is moved to `REORGED`, avoiding fabricated test wrapper objects.
- The deterministic settlement boundary itself remains unchanged and still requires canonical INCLUDED evidence and a successful receipt before terminal profit accounting.

#420 is the fresh certification for this repair and is currently in progress.

## 10. NEXT ATOMIC ACTION
Complete inspection of `#420`. On GREEN, move to hardening the live chain-observation adapter so approved Polygon transaction/receipt evidence collection is quorum-bound for recovered settlement decisions, with no production submission authority introduced.

**LIVE SIGNING = BLOCKED**  
**PUBLIC BROADCAST = BLOCKED**  
**LIVE CAPITAL = LOCKED**
