# Phase 19 Current Checkpoint

**Date:** 2026-09-14
**Branch:** `phase-19-e2e-harness`
**Latest implementation commit:** `e513cc65da5e7afcea9f6a57497930ef224713db`
**Phase:** 19
**Live execution:** LOCKED

## This checkpoint

The nonce layer has advanced from an in-memory policy/state model to a persistent SQLite adapter with atomic writer transactions and process-concurrency coverage.

### Added
- `phantomx/sqlite_nonce_store.py`
- `tests/phase19/test_sqlite_nonce_store.py`
- `.github/workflows/phase19-tests.yml`

### Durable/concurrency invariants implemented
- persistent sender-specific nonce cursors
- unique `(sender, nonce)` reservation identity
- globally unique reservation IDs
- atomic reservation allocation under `BEGIN IMMEDIATE`
- observed chain pending nonce can advance the cursor but never roll it back
- state transitions are persisted atomically
- submitted/included/replaced states require transaction hashes
- replacement state requires `replacement_of`
- invalid transitions roll back without mutating the record
- state survives process restart through the database file
- concurrent local processes are serialized by SQLite writer transactions
- WAL + `synchronous=FULL` are configured for the local durable store

SQLite WAL is intentionally a **single-host** persistence boundary. It must not be placed on a network filesystem or treated as a multi-host database service. A future multi-host deployment must use a suitable transactional server database while preserving the same nonce invariants.

## Evidence boundary

The implementation and adversarial tests are committed, but **actual CI execution evidence is still open** at this checkpoint. No test-pass claim is made until GitHub Actions produces a successful run artifact/status.

No Polygon RPC, private-key signing, transaction broadcast, or live capital is enabled.

## Remaining nonce P0 work

1. actual GitHub Actions execution evidence
2. chain pending-nonce reconciliation integration against Polygon RPC
3. crash/restart recovery policy for in-flight signed/submitted records
4. replacement transaction fee-policy integration
5. dropped/reorg observation integration
6. transaction-record binding

Only after these gates are proven should signer/transaction-builder integration begin.

## Governance

`FAIL → FREEZE → FORENSIC → PATCH → REGRESSION → VERIFY → STATUS → NEXT`

Any unresolved P0 gate keeps live execution locked.
