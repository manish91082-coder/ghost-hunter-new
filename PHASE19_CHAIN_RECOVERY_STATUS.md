# Phase-19 Chain Nonce + In-Flight Recovery Status

## Scope completed in this increment

Branch: `phase-19-e2e-harness`

This increment advances the nonce layer from local durable persistence toward chain-aware recovery, while keeping all signing, submission, and live execution locked.

### Implemented

1. `phantomx/polygon_nonce.py`
   - validates Ethereum JSON-RPC `eth_getTransactionCount(sender, "pending")` responses;
   - read-only injected transport boundary, with no signing or broadcasting;
   - monotonic reconciliation: local nonce may advance to chain pending nonce but never roll back;
   - optional distinct-provider quorum requiring unique consensus before accepting a chain nonce observation;
   - malformed RPC/error/ambiguous provider observations fail closed.

2. `phantomx/recovery.py`
   - explicit pending/included/reverted/not-found/unknown transaction evidence states;
   - successful inclusion requires block and receipt evidence and gas accounting fields;
   - transaction hash must match the durable active transaction before state mutation;
   - missing transaction alone never proves a drop;
   - drop proof requires chain pending nonce to have advanced beyond the transaction nonce;
   - reorg proof requires changed canonical block identity plus receipt disappearance;
   - recovery returns explicit durable state transitions instead of silently mutating state.

3. `tests/phase19/test_polygon_nonce.py` and `tests/phase19/test_recovery.py`
   - adversarial coverage for malformed RPC data, quorum disagreement, monotonic reconciliation, pending/not-found hold, inclusion/revert, drop proof, hash mismatch, and reorg proof.

4. `requirements-phase19.txt` and `.github/workflows/phase19-tests.yml`
   - CI now installs the required Ethereum Keccak backend before running the Phase-19 suite.

## CI evidence

A first CI run exposed a genuine missing Keccak dependency and stale schema fixtures. Those failures were preserved, diagnosed, and repaired.

- Run `34829714048`: **failure**, 90 tests, 38 errors. Primary root causes: missing `Crypto` backend plus stale test fixtures/calls.
- Run `34829846933`: **failure**, 90 tests, 7 errors. Dependency and earlier stale fixtures were fixed; remaining failures were stale `Authorization` gas/fee fields.
- Run `34829892489`: **success** for repaired commit `e98cb2ec...`.
- Run `34829948489`: **success** for current status checkpoint commit `1e5e8598...`.

The latest verified Phase-19 workflow completed successfully. This is test evidence for the committed deterministic suite, not production-chain proof.

## Evidence boundary

No Polygon RPC call, signer operation, transaction submission, private relay call, or live-capital execution was performed by this increment.

## Current P0 blockers

1. Wire the read-only nonce adapter to approved Polygon RPC endpoints with provider/quorum policy.
2. Define startup crash/restart recovery for `RESERVED → SIGNED → SUBMITTED` records.
3. Add deterministic replacement fee-policy bounds and replacement authorization.
4. Add chain observation for dropped/replaced/reorged transactions and persist evidence.
5. Bind durable transaction records to `ExecutionIntent`, `Authorization`, calldata hash, nonce, and transaction hash.
6. Only after these gates: signer/transaction-builder integration.
7. Only after signer + exact EVM preflight + private-only relay + settlement reconciliation: any live submission.

## Safety lock

Live execution remains **LOCKED**.

Required governance loop remains:

`FAIL → FREEZE → FORENSIC → PATCH → REGRESSION → VERIFY → STATUS → NEXT`

A passing unit test, a successful receipt, or a positive expected PnL must never be treated as production proof by itself.
