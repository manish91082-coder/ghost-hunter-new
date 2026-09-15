# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Active branch HEAD: `941288f13b079ff417402ef46776b8c27d7f1359`
- Latest implementation-bearing commit currently observed: `ad04f49a2083e0de54949405016776753dea1fbb`
- Latest cleanup commits: `777c7cc7ed8a0055a1b5576828a8306d1b383890`, `941288f13b079ff417402ef46776b8c27d7f1359`
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, and quorum-bound read-only executor authority attestation.

## 4. MVP REPOSITORY CLEANUP
The active Phase-19 branch has been surgically reduced to the targeted Phase-19 implementation/test spine.

- Removed the obsolete `v2/` stack, including historical AI/training/live-runner/diagnostic scripts, old deployment helpers, generated outputs, and legacy state/config artifacts.
- Removed the obsolete `v3/` stack, including historical universal-engine/AI/training/live-runner/telemetry/deployment artifacts.
- Removed the legacy root Python package marker `__init__.py`.
- Removed the legacy `config/` directory, including `config/settings.json` and its embedded Telegram credential/config surface. Phase-19 does not use that legacy configuration layer; production configuration remains an external controlled input.
- Preserved the Phase-19 Solidity contract, tests, `phantomx/` execution-integrity modules, Phase-19 test suite, workflow, requirements, project details, and canonical status/checkpoint evidence.

**Security note:** a Telegram bot token was present in the removed legacy settings file. Deleting it from the active tree does not revoke a credential that may have been exposed in Git history. The credential should be revoked/rotated outside the repository.

## 5. CURRENT AUTHORITY-PROOF HARDENING
`phantomx/executor_authority.py` provides `observe_executor_authority_quorum(...)`.

The quorum observer verifies Polygon chain identity on every configured provider, chooses one common observation block, reads executor `owner()` and runtime bytecode from every provider at that identical block, requires configured provider quorum on owner + runtime-code hash, rejects duplicate identities/wrong chain/insufficient agreement/ambiguous splits, and returns the immutable `ExecutorAuthorityEvidence`.

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
- Run `#275`: Python gate failed only on a brittle sorted-list assertion in the quorum test; 413 tests, 1 failure.
- Repair commit `e8ded6459a8d7a070310f49481f335043617650e` corrected the assertion.
- Run `#276`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 Polygon fork execution probe + 413/413 Python.

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

**Atomic task:** surgical repository cleanup to remove obsolete stacks/config/data without changing the Phase-19 execution-integrity architecture.

**Cleanup evidence:**
- Branch HEAD is `941288f13b079ff417402ef46776b8c27d7f1359`.
- Commit `777c7cc7ed8a0055a1b5576828a8306d1b383890` removes obsolete `v2/` and `v3/` stacks from the MVP branch.
- Commit `941288f13b079ff417402ef46776b8c27d7f1359` removes the legacy `config/` directory and root `__init__.py`.
- The active Phase-19 workflow installs `requirements-phase19.txt`, compiles `contracts`, runs the Phase-19 EVM harness, Polygon fork smoke/execution probes, and discovers tests under `tests/phase19`; the removed v2/v3/config stacks are not part of that workflow definition.

**Important:** the cleanup itself has not yet received a fresh post-cleanup CI result in the current evidence. Therefore current HEAD is **CLEANED BUT NOT YET RE-CERTIFIED**.

**Replacement hardening remains:** the `ad04f49...` replacement-coordinator change is still an implementation-bearing unverified change until fresh CI certifies a current-head build. The missing nullable durable-nonce `tx_hash` regression remains a next engineering gate.

**Authority/input finding:**
- Historical project material records `0x24056bCA6538693aE94Cc97E82f21Ee4EC7f128` as a PhantomXV2FlashLoanExecutor deployment candidate, but the same material explicitly marks it NOT YET PROVEN LIVE and requires chain, bytecode, interface, owner, domain, and runtime-code-hash verification.
- Historical public Polygon RPC endpoints also exist in older runtime notes, but they are not an approved production quorum.
- `common/active_rpc.txt` is not being promoted into production authority.

**Decision:** repository cleanup is now complete for the clearly obsolete v2/v3/config surfaces. Do not delete Phase-19 status/evidence documents merely to reduce file count; those are part of continuity and certification evidence. Next gate is fresh full Phase-19 CI against the cleaned HEAD, followed by the nullable-durable-`tx_hash` replacement regression before any promotion to verified.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
