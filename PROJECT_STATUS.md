# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `a1f76fcda0ff066b43a2dc0f19e08d682e98657b`
- Private-relay HTTP transport: `b7789d8da6c1eea70cc86e0ee5dd04dac3895694`
- Production private-relay assembly repair: `a9becb61ca05eee76a9123ff8d8be3d6fd9a97b8`
- Private-relay consumer/ambiguity tests: `fec3836fb7f18dab6cbe2cd2f626fbc36e5132aa`
- Latest relay secrecy/fallback-audit repair: `a1f76fcda0ff066b43a2dc0f19e08d682e98657b`
- Certified execution-surface baseline: `80c7675a006e4f8f5aeece4606ef7fd8b99d5851`, run `#395` GREEN
- Authority freshness/replay: `ea4e74dfb9a034c96faa9cd242055263c90bce0f`
- Authority reuse policy: `6f7b329fcffe40fc81fee8d95779a8d9751450be`
- Execution coordinator freshness: `53c84152a3df0407b3d37eaf4fee3577481b8829`
- Replacement coordinator freshness: `97d25cd024de1bf1e50c547ee9ceef924cb240cc`
- Signer freshness: `7b8314a11490921b02240b27175304aa1f6d3687`
- Signer freshness tests: `ea93238a9461db63bf02bc0993a170071179bc96`
- Production authority operator audit CLI: `f02e6db75ca27a061372f956defbee90f2de0d97`
- Production authority static surface audit: `dadd4c5b11261220f4b5bc17f7ce0d2f523d6721`
- Polygon RPC HTTP transport: `4a8e8338884f2bc63002d71d3e9984d07bdfd427`
- Certified freshness integration: run `#393` GREEN, 477/477 Python
- Certified production execution surface: run `#395` GREEN, 484/484 Python
- Private-relay boundary initial CI `#398`: **FAILED**, 485 Python tests with 1 failure and 1 import error; all non-Python stages passed
- Relay repair/consumer CI `#401`: **FAILED**, 500 Python tests with 2 assertion failures; all non-Python stages passed
- Fresh CI for `a1f76fc...`: pending
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

The high-level private submission boundary accepts governed immutable signed artifacts, revalidates executor authority before network I/O, requires an explicitly private relay, and has no public fallback. fileciteturn1039file0L2-L2

The Polygon read transport remains read-only; write/submission methods are blocked before network I/O. fileciteturn1022file0L2-L2

The dedicated private-relay transport accepts only non-empty raw signed transaction bytes, sends only `eth_sendRawTransaction`, requires HTTPS and explicit private assertion, separates authentication from endpoint configuration, and validates the returned transaction hash. fileciteturn1056file0L2-L2

The production relay configuration now keeps optional authentication material out of routine object representations, while the assembly audit checks the actual absence of public transport construction rather than rejecting the documentation word `fallback`.

## 4. CI CERTIFICATION PATH
Certified historical gates include signer repair `#349`, signer runbook `#360`, Polygon transport `#364`, production authority assembly `#367`, authority CLI `#371`, provenance `#373/#376`, freshness/reuse `#378/#379/#380`, execution/replacement/signer freshness `#393`, and repository production execution surface `#395`.

Run `#398` is preserved as failure evidence for the initial private-relay implementation: the Python stage recorded one import error and one surface-audit failure while compile, EVM, Polygon smoke, and Polygon execution probe passed. fileciteturn1054file0L2-L2

Run `#401` then proved the import/surface repairs worked, but exposed two remaining test-contract issues: the production relay configuration repr still exposed the authentication token, and the assembly audit used an over-broad `fallback` string assertion. The authoritative log recorded 500 Python tests with exactly these two failures; every non-Python workflow stage remained green. fileciteturn1066file0L2-L2

Both issues are repaired in `a1f76fc...`. Fresh CI for that exact head is pending and no GREEN conclusion is claimed yet.

## 5. CURRENT SIGNER IDENTITY GATE
The signer exposes a non-secret cryptographic challenge proof. External verification recovers the Ethereum address and requires exact equality with the expected signer address without private-key access.

The mechanism and runbook are CI-certified, but actual production signer identity remains **NOT PROVEN** until controlled externally held evidence is independently verified.

Signer freshness also requires exact executor/signer authority identity and bounded authority freshness before signing.

## 6. CURRENT POLYGON AUTHORITY / PRIVATE RELAY GATES
`phantomx/production_authority.py` consumes only explicit operator-supplied Polygon HTTPS endpoints, quorum, executor address, and expected signer address.

Authority evidence records actual attesting provider names in its canonical digest, and reusable authority evidence requires exact binding plus bounded freshness.

`scripts/observe_production_authority.py` is read-only and emits canonical non-secret authority evidence.

`phantomx/private_submit.py` remains the only high-level raw relay submission boundary. It requires a private relay and rechecks signed-artifact/authority identity immediately before network I/O. fileciteturn1039file0L2-L2

`phantomx/private_relay_http.py` is the dedicated low-level private-relay adapter and `phantomx/production_private_relay.py` is the explicit operator configuration assembly. No real production endpoint or relay credential has been introduced.

The regression layer verifies the assembly returns the dedicated private transport, execution submission does not directly call the low-level raw relay method, relay timeout/error responses fail closed, authentication is not leaked through repr, and the assembly has no public transport construction path.

This remains **implementation certification, not proof of an approved or connected production relay**.

## 7. CURRENT P0 BLOCKERS
1. Controlled production signer identity proof without exposing private-key material.
2. Controlled production Polygon provider authority proof using approved endpoints and intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like startup/recovery and settlement reorg evidence.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. CURRENT CHECKPOINT
Atomic task: repair and recertify the dedicated production private-relay boundary after CI exposed concrete test-contract mismatches.

Repair commits:
- `27d018e201d5b243b24896b6ca589b3f201c5e86` private relay auth repr hardening
- `a1f76fcda0ff066b43a2dc0f19e08d682e98657b` relay test/audit contract repair

Run `#401` is preserved as explicit failure evidence. Fresh CI for `a1f76fc...` is pending.

## 10. NEXT ATOMIC ACTION
Use the fresh CI result for `a1f76fc...`. Once GREEN, trace the complete relay acceptance/uncertainty path from `PrivateRelayHTTPTransport` through `private_submit.py` and `execution_submission.py`, then harden durable handling for an ambiguous relay result so a transport timeout cannot accidentally permit duplicate submission while the original transaction may already have been accepted.

**LIVE SIGNING = BLOCKED**  
**PUBLIC BROADCAST = BLOCKED**  
**LIVE CAPITAL = LOCKED**
