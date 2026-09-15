# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Active branch HEAD: `ad04f49a2083e0de54949405016776753dea1fbb`
- Latest implementation-bearing commit currently observed: `ad04f49a2083e0de54949405016776753dea1fbb`
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
Phase 19 includes strict realized-profit gating, deterministic all-in economics, Keccak hashing, immutable intent/auth/envelope binding, exact block-bound quotes, route simulation and topology commitment, loan optimization, EVM preflight, Governor, signer boundary, durable SQLite nonce/transaction state, atomic replacement/recovery coordination, private-only submission, receipt/reconciliation handling, Solidity executor controls, Polygon fork harness, and adversarial/regression coverage.

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, and quorum-bound read-only executor authority attestation.

## 4. CURRENT AUTHORITY-PROOF HARDENING
`phantomx/executor_authority.py` provides `observe_executor_authority_quorum(...)`.

The quorum observer verifies Polygon chain identity on every configured provider, chooses one common observation block, reads executor `owner()` and runtime bytecode from every provider at that identical block, requires provider consensus on owner + runtime-code hash at the configured quorum, rejects duplicate identities/wrong chain/insufficient agreement/ambiguous splits, and returns the existing immutable `ExecutorAuthorityEvidence`.

This is read-only and cannot sign or submit transactions.

## 5. VERIFIED CI EVIDENCE
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

## 6. CURRENT BLOCKERS / P0 GATES
1. Controlled production signer identity proof without exposing private key material.
2. Controlled production Polygon network/provider authority proof using explicitly approved production endpoints and the deployed executor address.
3. Production private relay capability with no public fallback.
4. Startup/recovery safety under production-like conditions.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, logs, and chat.

## 7. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 8. CURRENT CHECKPOINT

**Timestamp:** 2026-09-15

**Atomic task:** continuity audit of the active Phase-19 branch after discovering that the active branch has advanced beyond the previously certified quorum checkpoint.

**New active-branch evidence:**
- Active branch HEAD is `ad04f49a2083e0de54949405016776753dea1fbb`, commit `fix: allow signed drop before nonce tx hash is materialized`.
- The change is limited to `phantomx/replacement_coordinator.py` and permits a signed-but-never-submitted source transaction whose durable nonce row has not yet materialized a transaction hash, while still rejecting a conflicting non-null durable transaction hash. cite_internal_commit_placeholder
- No workflow run or combined status was returned for `ad04f49...`, so this newer implementation commit is **NOT independently CI-certified** in the currently observed evidence.

**Authority/input finding:**
- Historical Library material contains a prior PhantomXV2FlashLoanExecutor candidate `0x24056bCA6538693aE94Cc97E82f21Ee4EC7f128`, but the same record explicitly marks it NOT YET PROVEN LIVE and requires chain, bytecode, interface, owner, domain, and runtime-code-hash verification.
- Historical public Polygon RPC endpoints also exist in old runtime notes, but they are not an approved production quorum.
- `common/active_rpc.txt` remains an Ethereum endpoint and is not promoted into production authority.

**Decision:** The replacement-coordinator change is useful hardening but remains an **UNVERIFIED CURRENT-HEAD CHANGE** until a fresh full Phase-19 CI run certifies it. P19-AUTH-02 remains **BLOCKED** because controlled production provider/signing inputs are still absent.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** obtain a fresh full CI certification for current HEAD `ad04f49...` before treating that branch state as green; independently maintain the production-authority gate as blocked until approved provider quorum + intended executor identity + expected signer identity are supplied.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**
