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
   - successful inclusion requires block + receipt evidence and gas accounting fields;
   - transaction hash must match the durable active transaction before state mutation;
   - missing transaction alone never proves a drop;
   - drop proof requires chain pending nonce to have advanced beyond the transaction nonce;
   - reorg proof requires changed canonical block identity plus receipt disappearance;
   - recovery returns explicit durable state transitions instead of silently mutating state.

3. `tests/phase19/test_polygon_nonce.py`
   - RPC quantity parsing;
   - RPC error fail-closed behavior;
   - monotonic reconciliation;
   - unique quorum consensus;
   - no-quorum rejection.

4. `tests/phase19/test_recovery.py`
   - pending hold;
   - not-found hold;
   - successful inclusion;
   - reverted inclusion;
   - active-hash mismatch rejection;
   - nonce-consumption drop proof;
   - reorg proof and negative case;
   - durable state application after explicit proof.

## Evidence boundary

Git commits prove implementation was written to the repository. They do **not** prove that the test suite passed. The repository's Phase-19 GitHub Actions workflow exists, but no successful workflow run has been independently verified yet.

No Polygon RPC call, signer operation, transaction submission, private relay call, or live-capital execution was performed by this increment.

## Current P0 blockers

1. Verify GitHub Actions execution and preserve run evidence.
2. Wire the read-only nonce adapter to approved Polygon RPC endpoints with provider/quorum policy.
3. Define crash/restart recovery for `RESERVED → SIGNED → SUBMITTED` records, including startup reconciliation.
4. Add deterministic replacement fee-policy bounds without authorizing arbitrary fee escalation.
5. Add chain observation for dropped/reorged/replaced transactions and persist the resulting evidence.
6. Bind durable transaction records to `ExecutionIntent`, `Authorization`, calldata hash, nonce, and transaction hash.
7. Only after those gates: signer integration.
8. Only after signer + preflight + private-only relay + settlement gates: any live submission.

## Safety lock

Live execution remains **LOCKED**.

Required governance loop remains:

`FAIL → FREEZE → FORENSIC → PATCH → REGRESSION → VERIFY → STATUS → NEXT`

A passing unit test, a successful receipt, or a positive expected PnL must never be treated as production proof by itself.
