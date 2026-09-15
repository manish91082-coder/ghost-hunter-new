# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation commit: `6697c38cd27648a73a17bcd3f4928f59df1b4df0`
- Certified execution-surface commit: `80c7675a006e4f8f5aeece4606ef7fd8b99d5851`, run `#395` GREEN
- Production Polygon authority assembly: `2492cd97c750bc3aa37b30d25e9bc9fcb2fb0864`
- Authority freshness/replay: `ea4e74dfb9a034c96faa9cd242055263c90bce0f`
- Execution coordinator freshness: `53c84152a3df0407b3d37eaf4fee3577481b8829`
- Replacement coordinator freshness: `97d25cd024de1bf1e50c547ee9ceef924cb240cc`
- Signer freshness: `7b8314a11490921b02240b27175304aa1f6d3687`
- Signer freshness tests: `ea93238a9461db63bf02bc0993a170071179bc96`
- Production authority operator audit CLI: `f02e6db75ca27a061372f956defbee90f2de0d97`
- Production authority static surface audit: `dadd4c5b11261220f4b5bc17f7ce0d2f523d6721`
- Production execution surface audit: `80c7675a006e4f8f5aeece4606ef7fd8b99d5851`
- Polygon RPC HTTP transport: `4a8e8338884f2bc63002d71d3e9984d07bdfd427`
- Latest private-relay HTTP transport: `b7789d8da6c1eea70cc86e0ee5dd04dac3895694`
- Production private-relay assembly: `a9becb61ca05eee76a9123ff8d8be3d6fd9a97b8`
- Private-relay regression suite: `d94aa847511c2538551613a065ac9db6613355d5`
- Latest private-relay CI `#398`: **FAILED**, 485 Python tests with 1 failure and 1 import error; compile, 14/14 EVM, 3/3 Polygon smoke, 1/1 Polygon execution probe passed
- Repair commits: `a9becb61...` fixes adapter import binding; `6697c38c...` aligns the production surface audit with the dedicated submission transport
- Fresh repaired-head CI: **PENDING**
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

The Polygon read transport is separately constrained to a read-only allowlist; its raw-transaction RPC string is deny-list policy only. fileciteturn1022file0L2-L2

The dedicated private-relay transport accepts raw signed transaction bytes and emits only `eth_sendRawTransaction` to an explicitly configured private endpoint. Authentication is supplied separately and hidden from routine representation.

## 4. CI CERTIFICATION PATH
Certified historical gates include signer repair `#349`, signer runbook `#360`, Polygon transport `#364`, production authority assembly `#367`, authority CLI `#371`, provenance `#373/#376`, freshness/reuse `#378/#379/#380`, execution/replacement/signer freshness `#393`, and repository production execution surface audit `#395`.

Run `#398` is the failure evidence for the first private-relay implementation. Its Python stage recorded 485 tests, 1 failure, and 1 import error; compile, 14/14 EVM, 3/3 Polygon smoke, and 1/1 Polygon execution probe all passed. The import error was the incorrect production assembly module name, and the static audit needed to recognize the dedicated submission transport as the one legitimate raw-transaction sender.

Those defects were repaired in `a9becb61...` and `6697c38c...`. Fresh certification of the repaired head is pending.

## 5. CURRENT SIGNER IDENTITY GATE
The signer exposes a non-secret cryptographic challenge proof and external verification path. The mechanism is CI-certified, but actual production signer identity remains **NOT PROVEN** until controlled externally held evidence is independently verified.

Signer-bound authority freshness and exact executor/signer identity are enforced before signing.

## 6. CURRENT POLYGON AUTHORITY / PRIVATE RELAY GATES
`phantomx/production_authority.py` consumes only explicit operator-supplied Polygon HTTPS endpoints, quorum, executor address, and expected signer address. fileciteturn1040file0L2-L2

Authority evidence records actual attesting provider names in its canonical digest, and reuse requires exact binding plus bounded freshness.

`scripts/observe_production_authority.py` is read-only and emits canonical non-secret authority evidence.

`phantomx/private_submit.py` remains the only high-level raw relay submission boundary. It requires a private relay and verifies the signed artifact/authority envelope immediately before network I/O. fileciteturn1039file0L2-L2

`phantomx/private_relay_http.py` is the dedicated low-level private relay HTTP adapter. It requires HTTPS, refuses embedded endpoint credentials, explicitly asserts private mode, and validates the returned transaction hash. `phantomx/production_private_relay.py` loads only explicit `PHANTOMX_PRIVATE_RELAY_JSON` plus optional `PHANTOMX_PRIVATE_RELAY_AUTH_TOKEN`. No real production relay endpoint or credential has been introduced.

This is **private-relay implementation certification work, not proof of an approved live production relay**.

## 7. CURRENT P0 BLOCKERS
1. Controlled production signer identity proof without exposing private-key material.
2. Controlled production Polygon provider authority proof using approved endpoints and the intended deployed executor.
3. Controlled production private relay proof using an actually approved relay endpoint and authentication, with no public fallback.
4. Production-like startup/recovery and settlement reorg evidence.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. CURRENT CHECKPOINT
Atomic task: explicit production private-relay configuration and dedicated HTTP submission boundary, with no real endpoint, credential, private key, live broadcast, or public fallback.

Implementation commits:
- `b7789d8da6c1eea70cc86e0ee5dd04dac3895694` private-relay HTTP transport
- `9add0739c6fd4035730cbfce7d0803e7116da3e7` initial production relay assembly
- `d94aa847511c2538551613a065ac9db6613355d5` regression suite
- `a9becb61ca05eee76a9123ff8d8be3d6fd9a97b8` import repair
- `6697c38cd27648a73a17bcd3f4928f59df1b4df0` surface audit repair

Run `#398` is explicit failure evidence; its exact defects are repaired. Fresh CI for `6697c38c...` is the current certification gate.

## 10. NEXT ATOMIC ACTION
After fresh CI, trace every submission consumer through `production_private_relay.py → private_submit.py → execution_submission.py`, then harden relay-response ambiguity and accepted-but-unconfirmed lifecycle handling.

**LIVE SIGNING = BLOCKED**  
**PUBLIC BROADCAST = BLOCKED**  
**LIVE CAPITAL = LOCKED**
