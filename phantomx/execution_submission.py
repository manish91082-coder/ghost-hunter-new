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

    A fresh authority observation is required at submission. The observation may
    be newer than signing-time evidence, but its stable executor owner/runtime
    identity must equal the identity committed into the signed artifact. This
    closes the signing-to-submission deployment drift window.
    """
    try:
        if submission_authority.observed_block < prepared.authority.observed_block:
            raise ExecutionSubmissionError("submission authority evidence predates signing authority evidence")
        if runtime_code_binding_hash(submission_authority).lower() != prepared.signed_transaction.executor_runtime_binding_hash.lower():
            raise ExecutionSubmissionError("submission executor runtime identity differs from signed artifact")

        # Re-check the durable lifecycle immediately before network I/O. A caller
        # may retry a prepared object after a previous successful submission;
        # that retry must not reach the relay once durable state is no longer
        # SIGNED. This prevents duplicate private relay attempts for the same
        # immutable signed artifact.
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
            if ExecutionState(row[1]) is not ExecutionState.SIGNED:
                raise ExecutionSubmissionError("durable transaction is not in SIGNED state")

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
                (ExecutionState.PRIVATE_SUBMITTED.value, prepared.transaction_record.record_hash(), ExecutionState.SIGNED.value),
            )
            db.execute(
                "UPDATE nonce_records SET status=?, tx_hash=? WHERE sender=? AND nonce=? AND status=?",
                (NonceStatus.SUBMITTED.value, submission.transaction_hash.lower(), row[3], int(row[4]), NonceStatus.SIGNED.value),
            )
            db.execute("COMMIT")
    except Exception as exc:
        raise ExecutionSubmissionError(
            "private relay accepted the transaction but durable SUBMITTED persistence failed; hold and reconcile on-chain"
        ) from exc

    return SubmittedExecution(
        prepared=prepared,
        submission=submission,
        transaction_state=ExecutionState.PRIVATE_SUBMITTED,
        nonce_state=NonceStatus.SUBMITTED,
    )
