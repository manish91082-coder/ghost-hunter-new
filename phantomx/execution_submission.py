"""Private submission adapter for the durable Phase-19 execution record."""
from __future__ import annotations

from dataclasses import dataclass

from .durable_nonce import NonceStatus
from .execution import ExecutionState
from .execution_coordinator import PreparedExecution
from .executor_authority import ExecutorAuthorityEvidence, runtime_code_binding_hash
from .private_submit import PrivateRelay, PrivateSubmission, submit_governed_transaction
from .sqlite_execution_store import SQLiteExecutionStore


class ExecutionSubmissionError(RuntimeError):
    """Raised when private submission or durable persistence fails."""


@dataclass(frozen=True)
class SubmittedExecution:
    prepared: PreparedExecution
    submission: PrivateSubmission
    transaction_state: ExecutionState
    nonce_state: NonceStatus


def submit_prepared_execution(
    *,
    store: SQLiteExecutionStore,
    prepared: PreparedExecution,
    relay: PrivateRelay,
    now: int,
    submission_authority: ExecutorAuthorityEvidence,
) -> SubmittedExecution:
    """Submit one immutable signed artifact privately, then persist SUBMITTED.

    The durable record enters ``SUBMISSION_IN_FLIGHT`` in a committed SQLite
    transaction immediately before network I/O. Once that state is durable,
    retries are blocked until chain reconciliation proves the outcome. This
    prevents a relay timeout or connection failure after possible acceptance
    from being mistaken for a safe pre-submission retry opportunity.
    """
    try:
        if submission_authority.observed_block < prepared.authority.observed_block:
            raise ExecutionSubmissionError("submission authority evidence predates signing authority evidence")
        if runtime_code_binding_hash(submission_authority).lower() != prepared.signed_transaction.executor_runtime_binding_hash.lower():
            raise ExecutionSubmissionError("submission executor runtime identity differs from signed artifact")
        if not prepared.governor.approved:
            raise ExecutionSubmissionError("governor did not approve private submission")
        if now < 0 or prepared.assembly.intent.deadline < now:
            raise ExecutionSubmissionError("execution deadline has expired")
        if not getattr(relay, "is_private", False):
            raise ExecutionSubmissionError("configured relay is not explicitly private")
        relay_name = getattr(relay, "name", None)
        if not isinstance(relay_name, str) or not relay_name:
            raise ExecutionSubmissionError("private relay identity is required")

        # Re-check the durable lifecycle immediately before network I/O. A caller
        # may retry a prepared object after a previous successful submission or
        # after an ambiguous relay outcome; neither case may reach the relay
        # while the durable record is no longer exactly SIGNED.
        with store._connect() as db:
            row = db.execute(
                "SELECT intent_hash,state,tx_hash,sender,nonce FROM transaction_records WHERE record_hash=?",
                (prepared.transaction_record.record_hash(),),
            ).fetchone()
            if row is None:
                raise ExecutionSubmissionError("durable transaction record disappeared before private submission")
            if row[0].lower() != prepared.assembly.intent_hash.lower() or row[2].lower() != prepared.signed_transaction.transaction_hash.lower():
                raise ExecutionSubmissionError("durable transaction identity changed before private submission")
            if ExecutionState(row[1]) is not ExecutionState.SIGNED:
                raise ExecutionSubmissionError("durable transaction is not in SIGNED state before private submission")

            nrow = db.execute(
                "SELECT intent_hash,status,tx_hash FROM nonce_records WHERE sender=? AND nonce=?",
                (row[3], int(row[4])),
            ).fetchone()
            if nrow is None:
                raise ExecutionSubmissionError("durable nonce record disappeared before private submission")
            if nrow[0].lower() != prepared.assembly.intent_hash.lower() or nrow[1] != NonceStatus.SIGNED.value:
                raise ExecutionSubmissionError("durable nonce identity/state changed before private submission")
            if nrow[2] is not None and nrow[2].lower() != prepared.signed_transaction.transaction_hash.lower():
                raise ExecutionSubmissionError("durable nonce transaction hash conflicts with signed artifact before private submission")

            db.execute("BEGIN IMMEDIATE")
            updated = db.execute(
                "UPDATE transaction_records SET state=? WHERE record_hash=? AND state=?",
                (
                    ExecutionState.SUBMISSION_IN_FLIGHT.value,
                    prepared.transaction_record.record_hash(),
                    ExecutionState.SIGNED.value,
                ),
            ).rowcount
            if updated != 1:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise ExecutionSubmissionError("durable transaction could not enter submission in-flight state")
            db.execute("COMMIT")

        try:
            submission = submit_governed_transaction(
                relay=relay,
                signed_transaction=prepared.signed_transaction,
                governor=prepared.governor,
                intent=prepared.assembly.intent,
                authorization=prepared.assembly.authorization,
                envelope=prepared.assembly.envelope,
                executor_authority=submission_authority,
                now=now,
            )
        except Exception as exc:
            # Do not revert to SIGNED. The durable IN_FLIGHT marker is the
            # crash-safe fence against duplicate relay submission. Operators
            # or recovery automation must reconcile the signed tx hash on-chain.
            raise ExecutionSubmissionError(
                "private relay outcome is uncertain; durable submission remains IN_FLIGHT and must be reconciled on-chain"
            ) from exc
    except Exception as exc:
        if isinstance(exc, ExecutionSubmissionError):
            raise
        raise ExecutionSubmissionError(str(exc)) from exc

    try:
        with store._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT intent_hash,state,tx_hash,sender,nonce FROM transaction_records WHERE record_hash=?",
                (prepared.transaction_record.record_hash(),),
            ).fetchone()
            if row is None:
                raise ExecutionSubmissionError("durable transaction record disappeared before submission persistence")
            if row[0].lower() != prepared.assembly.intent_hash.lower() or row[2].lower() != submission.transaction_hash.lower():
                raise ExecutionSubmissionError("durable transaction identity changed before submission persistence")
            if ExecutionState(row[1]) is not ExecutionState.SUBMISSION_IN_FLIGHT:
                raise ExecutionSubmissionError("durable transaction is not in submission in-flight state")

            nrow = db.execute(
                "SELECT intent_hash,status,tx_hash FROM nonce_records WHERE sender=? AND nonce=?",
                (row[3], int(row[4])),
            ).fetchone()
            if nrow is None:
                raise ExecutionSubmissionError("durable nonce record disappeared before submission persistence")
            if nrow[0].lower() != prepared.assembly.intent_hash.lower() or nrow[1] != NonceStatus.SIGNED.value:
                raise ExecutionSubmissionError("durable nonce identity/state changed before submission persistence")
            if nrow[2] is not None and nrow[2].lower() != submission.transaction_hash.lower():
                raise ExecutionSubmissionError("durable nonce transaction hash conflicts with submitted hash")

            db.execute(
                "UPDATE transaction_records SET state=? WHERE record_hash=? AND state=?",
                (ExecutionState.PRIVATE_SUBMITTED.value, prepared.transaction_record.record_hash(), ExecutionState.SUBMISSION_IN_FLIGHT.value),
            )
            db.execute(
                "UPDATE nonce_records SET status=?, tx_hash=? WHERE sender=? AND nonce=? AND status=?",
                (NonceStatus.SUBMITTED.value, submission.transaction_hash.lower(), row[3], int(row[4]), NonceStatus.SIGNED.value),
            )
            db.execute("COMMIT")
    except Exception as exc:
        raise ExecutionSubmissionError(
            "private relay accepted the transaction but durable SUBMITTED persistence failed; durable record remains held for on-chain reconciliation"
        ) from exc

    return SubmittedExecution(
        prepared=prepared,
        submission=submission,
        transaction_state=ExecutionState.PRIVATE_SUBMITTED,
        nonce_state=NonceStatus.SUBMITTED,
    )
