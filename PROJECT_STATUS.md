# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Active branch HEAD: `eb9ee0c6b62e349500f177b8fa761673ce1a999b`
- Latest implementation-bearing commit observed: `eb9ee0c6b62e349500f177b8fa761673ce1a999b` (replacement regression)
- Prior implementation-bearing hardening: `ad04f49a2083e0de54949405016776753dea1fbb`
- Recent cleanup/docs commits: `777c7cc7ed8a0055a1b5576828a8306d1b383890`, `941288f13b079ff417402ef46776b8c27d7f1359`, `01b20c5a6713aa84778e88fda07b9c71aaa4f18a`
- Phase: Phase 19 execution-integrity / E2E policy harness
- Live mainnet execution: **BLOCKED**
- Live capital authorization: **BLOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## 1. NON-NEGOTIABLE SAFETY / CONTROL RULES
- Evidence first; contradictory or missing evidence is UNKNOWN/BLOCKED.
- Fail closed on quote, proof, simulation, authorization, nonce, signer, relay, authority, or settlement inconsistency.
- AI is advisory and cannot override deterministic economics, preflight, governance, authorization, or settlement.
- Private execution has no public fallback.
- Live capital remains locked until every P0 gate has reproducible evidence.
- No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification.

## 2. CANONICAL PRODUCTION SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

Initial scope: Polygon, Aave V3, QuickSwap V2, Uniswap V3, USDC/WETH/WMATIC/WBTC, direct two-leg `A → B → A`.

## 3. VERIFIED IMPLEMENTATION CAPABILITIES
Phase 19 includes strict realized-profit gating, deterministic all-in economics, Keccak hashing, immutable intent/auth/envelope binding, exact block-bound quotes, route simulation and topology commitment, loan optimization, EVM preflight, Governor, signer boundary, durable SQLite nonce/transaction state, atomic replacement/recovery coordination, private-only submission, chain/recovery/reorg/replacement handling, receipt reconciliation, Solidity executor controls, Polygon fork harness, and adversarial/regression coverage.

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, and nullable durable-nonce-hash replacement coverage.

## 4. MVP REPOSITORY CLEANUP / CONSISTENCY
The active branch has been reduced to the targeted Phase-19 implementation/test spine.

- Removed obsolete `v2/` and `v3/` runtime/AI/training/deployment/state stacks.
- Removed legacy root `__init__.py` and obsolete secret-bearing `config/settings.json` configuration surface.
- Rewrote `PROJECT_DETAILS.md` to describe the current Phase-19 MVP instead of deleted legacy launchers/runners/AI artifacts.
- Preserved the Phase-19 Solidity contract, tests, `phantomx/` execution-integrity modules, workflow, requirements, and audit/continuity evidence.

**Security note:** the removed legacy settings file contained a Telegram bot token. Deletion does not revoke a credential that may exist in Git history; revoke/rotate that credential externally.

## 5. CURRENT AUTHORITY-PROOF HARDENING
`phantomx/executor_authority.py` provides `observe_executor_authority_quorum(...)`.

The quorum observer verifies Polygon chain identity on every configured provider, chooses one common observation block, reads executor `owner()` and runtime bytecode from every provider at that identical block, requires configured provider quorum on owner + runtime-code hash, rejects duplicate identities/wrong chain/insufficient agreement/ambiguous splits, and returns immutable `ExecutorAuthorityEvidence`.

This is read-only and cannot sign or submit transactions.

## 6. VERIFIED CI EVIDENCE
- Run `#258`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 402/402 Python.
- Run `#261`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 403/403 Python.
- Run `#262`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 403/403 Python.
- Run `#266`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 404/404 Python.
- Run `#268`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + 405/405 Python.
- Run `#269`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + 406/406 Python.
- Run `#270`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + 407/407 Python.
- Run `#273`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 Polygon fork execution probe + 408/408 Python.
- Run `#275`: Python gate failed only on a brittle sorted-list assertion; 413 tests, 1 failure.
- Repair commit `e8ded6459a8d7a070310f49481f335043617650e` corrected the assertion.
- Run `#276`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 Polygon fork execution probe + 413/413 Python.

**Current-head certification:** a fresh workflow run for `eb9ee0c6...` is required/awaited. The current GitHub connector did not expose a push-triggered workflow run for this commit at the time of this update, so no new pass is claimed.

## 7. CURRENT BLOCKERS / P0 GATES
1. Controlled production signer identity proof without exposing private key material.
2. Controlled production Polygon network/provider authority proof using explicitly approved production endpoints and the deployed executor address.
3. Production private relay capability with no public fallback.
4. Startup/recovery safety under production-like conditions.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, logs, and chat.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task:** lead-directed MVP integration/cleanliness audit, documentation alignment, and nullable durable-nonce replacement regression.

**New work completed:**
- `PROJECT_DETAILS.md` was replaced with a canonical Phase-19 architecture description because the prior file referenced deleted legacy launchers, runners, AI trainers, public-RPC execution and stale thresholds.
- `tests/phase19/test_replacement_coordinator.py` now explicitly tests a valid dropped source whose durable nonce row has `tx_hash=NULL`; replacement must proceed, then install the replacement transaction hash and `replacement_of` relationship atomically.
- The core store schema explicitly permits nullable `nonce_records.tx_hash`, while replacement persistence rejects only a conflicting non-null source hash. This aligns storage semantics with the coordinator hardening.

**Current verdict:** architecture is structurally coherent and the targeted Phase-19 core is present. However, current HEAD is **NOT YET CI-CERTIFIED** after the documentation/test changes. Connector status for the latest commit currently returns no exposed checks, so a pass is not claimed.

**Authority/input finding:**
- Historical project material still contains a candidate executor identity, but it is explicitly not live-proof; production authority remains blocked pending approved provider quorum + intended executor identity + expected signer identity.
- Historical public RPC endpoints are not promoted into production authority.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** obtain authoritative fresh CI evidence for `eb9ee0c6...`; inspect any failures; only then continue the MVP internal integration audit or advance to the highest-value unresolved production gate.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
