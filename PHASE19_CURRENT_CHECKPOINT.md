# Phase 19 Current Checkpoint

**Date:** 2026-09-14
**Branch:** `phase-19-e2e-harness`
**Latest implementation commit:** `fceea4fa6f7c34f055e6b233b5ae85cf88047b0c`
**Latest verified CI:** run `34832734965` on `fceea4fa6f7c34f055e6b233b5ae85cf88047b0c` → SUCCESS
**Phase:** 19
**Live execution:** LOCKED

## This checkpoint

Phase 19 now has a durable SQLite TransactionRecord persistence boundary. A signed-state record can be persisted with its intent hash, authorization fingerprint, nonce reservation, chain/sender/executor, exact calldata hash, gas envelope, transaction hash, lifecycle state and explicit replacement linkage. The store uses SQLite `BEGIN IMMEDIATE`, WAL and `synchronous=FULL`, matching the single-host crash-safety boundary of the durable nonce store.

### Added / hardened
- `phantomx/sqlite_transaction_store.py`
- `tests/phase19/test_sqlite_transaction_store.py`
- `phantomx/transaction_record.py` now accepts an explicit `now` parameter for deadline validation
- `TransactionRecord.record_hash()` is now a stable identity hash; `state_hash()` captures identity plus mutable lifecycle state

### Durable TransactionRecord invariants
- exact ExecutionIntent hash required
- sender, nonce and reservation identity must match the bound nonce
- new durable records start only at `SIGNED`
- transaction hashes are unique and validated as complete 32-byte identifiers
- stored record identity is recomputed on load
- lifecycle transitions are atomic and invalid transitions leave state unchanged
- terminal states cannot restart
- restart reloads the exact record and lifecycle state
- replacements preserve sender and nonce and require exact `replacement_of` linkage to an existing replaceable transaction
- replacement source must be `SIGNED`, `PRIVATE_SUBMITTED` or `PENDING`
- no signer, RPC observer, broadcaster or relay authority exists in this store

### Adversarial / recovery coverage
- create + restart persistence
- duplicate transaction hash rejection
- intent mutation rejection
- nonce mutation rejection
- lifecycle progression across repeated restarts
- invalid transition non-mutation
- terminal-state restart rejection
- exact replacement linkage
- wrong replacement source rejection
- crash-like restart preserving an incomplete signed record
- stable identity hash versus state hash

## CI evidence

GitHub Actions run `34832734965` executed the complete Phase-19 unittest suite successfully for commit `fceea4fa6f7c34f055e6b233b5ae85cf88047b0c`. The preceding run `34832642716` failed on an identity/state-hash design defect; that failure was diagnosed from CI logs, patched, and superseded by the green run. No failed run was hidden or overwritten.

The verified green run covered **110 tests**.

## Evidence boundary

This is deterministic/unit-level and local persistence evidence. It is not Polygon fork proof or production execution proof.

No live Polygon RPC execution, private-key signing, transaction broadcast, private relay submission, or live capital execution was performed.

## Remaining P0 work

1. deterministic replacement fee-policy bounds and replacement authorization
2. durable chain observation for dropped/replaced/reorged transactions
3. atomic startup crash/restart reconciliation across nonce + transaction records
4. approved Polygon RPC integration with provider/quorum policy
5. production signer/transaction-builder integration only after the above gates
6. exact EVM preflight immediately before signing
7. private-only relay with no public fallback
8. receipt settlement reconciliation and realized net PnL proof
9. Polygon fork/E2E adversarial proof

**Live execution remains LOCKED.**

## Governance

`FAIL → FREEZE → FORENSIC → PATCH → REGRESSION → VERIFY → STATUS → NEXT`

Implementation commit ≠ test proof ≠ fork proof ≠ production proof.
