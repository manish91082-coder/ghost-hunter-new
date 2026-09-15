"""Fail-closed durable replacement preparation for Phase 19.

A replacement is a new signed transaction using the same sender+nonce and
exact execution intent. It may only be prepared after explicit durable drop or
replacement evidence. This module performs no submission.
"""
from __future__ import annotations

from dataclasses import dataclass

from .durable_nonce import NonceStatus
from .economic_proof import EconomicProof
from .execution import ExecutionState
from .execution_assembly import ExecutionAssembly, assemble_execution
from .evm_preflight import EVMPreflightResult, preflight_execution
from .executor_authority import ExecutorAuthorityError, ExecutorAuthorityEvidence, verify_executor_authority
from .governor import GovernorDecision, GovernorPolicy, govern_execution
from .nonce_binding import BoundNonce
from .replacement_policy import ReplacementAuthorization, ReplacementFeePolicy
from .signer import SignedTransaction, TransactionSigner, sign_governed_transaction
from .sqlite_execution_store import SQLiteExecutionStore
from .transaction_record import TransactionRecord, authorization_hash, build_signed_record


class ReplacementCoordinatorError(RuntimeError):
    """Raised when replacement preparation cannot be completed safely."""


@dataclass(frozen=True)
class PreparedReplacement:
    """Immutable replacement evidence persisted at the signer boundary."""

    source: TransactionRecord
    assembly: ExecutionAssembly
    authority: ExecutorAuthorityEvidence
    preflight: EVMPreflightResult
    governor: GovernorDecision
    bound_nonce: BoundNonce
    signed_transaction: SignedTransaction
    transaction_record: TransactionRecord
    replacement_authorization: ReplacementAuthorization


def _same_hash(left: str, right: str) -> bool:
    return left.lower() == right.lower()


def prepare_replacement_execution(
    *,
    store: SQLiteExecutionStore,
    source_record_hash: str,
    simulation,
    economic_proof: EconomicProof,
    replacement_policy: ReplacementFeePolicy,
    executor: str,
    sender: str,
    executor_authority: ExecutorAuthorityEvidence,
    deadline: int,
    first_on_quickswap: bool,
    amount_out_min_first: int,
    amount_out_min_second: int,
    minimum_surplus: int,
    aave_pool: str,
    quickswap_router: str,
    uniswap_v3_router: str,
    gas_limit: int,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
    policy: GovernorPolicy,
    signer: TransactionSigner,
    now: int,
    current_block_number: int,
    ai_rank=None,
) -> PreparedReplacement:
    """Prepare one new transaction for an explicitly replaceable source."""
    if now < 0 or current_block_number < 0:
        raise ReplacementCoordinatorError("time and block must be non-negative")

    source = store.get_transaction(source_record_hash)
    if source.state not in {ExecutionState.DROPPED, ExecutionState.REPLACED}:
        raise ReplacementCoordinatorError("source transaction is not in a replaceable durable state")
    if source.sender.lower() != sender.lower() or source.executor.lower() != executor.lower():
        raise ReplacementCoordinatorError("replacement sender/executor does not match source")
    if source.nonce < 0:
        raise ReplacementCoordinatorError("source nonce cannot be negative")

    nonce = store.get_nonce(sender, source.nonce)
    if nonce.reservation_id != source.reservation_id:
        raise ReplacementCoordinatorError("durable nonce reservation does not match source")
    # A signed-but-never-submitted transaction may not yet have materialized its
    # tx hash in the durable nonce row. That is safe because the durable source
    # transaction record itself already binds the exact signed transaction hash.
    # Once a nonce tx hash exists it must match the source exactly.
    if nonce.tx_hash is not None and not _same_hash(nonce.tx_hash, source.tx_hash):
        raise ReplacementCoordinatorError("durable nonce active transaction does not match source")
    if nonce.status not in {NonceStatus.DROPPED, NonceStatus.REPLACED}:
        raise ReplacementCoordinatorError("durable nonce is not in an explicitly replaceable state")

    try:
        verify_executor_authority(
            executor_authority,
            chain_id=simulation.chain_id,
            executor=executor,
            sender=sender,
            minimum_observed_block=simulation.block_number,
        )
    except ExecutorAuthorityError as exc:
        raise ReplacementCoordinatorError(str(exc)) from exc

    try:
        replacement_policy.authorize(
            source.max_fee_per_gas,
            source.max_priority_fee_per_gas,
            max_fee_per_gas,
            max_priority_fee_per_gas,
        )
    except ValueError as exc:
        raise ReplacementCoordinatorError(str(exc)) from exc

    assembly = assemble_execution(
        simulation=simulation,
        economic_proof=economic_proof,
        executor=executor,
        sender=sender,
        nonce=source.nonce,
        deadline=deadline,
        first_on_quickswap=first_on_quickswap,
        amount_out_min_first=amount_out_min_first,
        amount_out_min_second=amount_out_min_second,
        minimum_surplus=minimum_surplus,
        aave_pool=aave_pool,
        quickswap_router=quickswap_router,
        uniswap_v3_router=uniswap_v3_router,
        gas_limit=gas_limit,
        max_fee_per_gas=max_fee_per_gas,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
    )
    if not _same_hash(assembly.intent_hash, source.intent_hash):
        raise ReplacementCoordinatorError("replacement cannot mutate execution intent")

    bound_record = BoundNonce(
        reservation_id=source.reservation_id,
        sender=source.sender,
        nonce=source.nonce,
        intent_hash=assembly.intent.intent_hash(),
    )
    preflight = preflight_execution(
        intent=assembly.intent,
        authorization=assembly.authorization,
        envelope=assembly.envelope,
        simulation=assembly.simulation,
        economic_proof=assembly.economic_proof,
        now=now,
        expected_route_commitment=assembly.bound_call.route_commitment,
        executor_authority=executor_authority,
    )
    governor = govern_execution(
        policy=policy,
        preflight=preflight,
        intent=assembly.intent,
        envelope=assembly.envelope,
        economic_proof=assembly.economic_proof,
        executor_authority=executor_authority,
        lifecycle_state=ExecutionState.VERIFIED,
        nonce_reserved=True,
        replay_consumed=False,
        current_block_number=current_block_number,
        now=now,
        ai_rank=ai_rank,
    )
    if not governor.approved:
        raise ReplacementCoordinatorError(f"governor blocked replacement: {governor.reason}")

    try:
        signed_transaction = sign_governed_transaction(
            signer=signer,
            governor=governor,
            intent=assembly.intent,
            authorization=assembly.authorization,
            envelope=assembly.envelope,
            executor_authority=executor_authority,
            now=now,
        )
    except Exception as exc:
        raise ReplacementCoordinatorError(str(exc)) from exc

    replacement_tx_hash = signed_transaction.transaction_hash
    replacement_auth = ReplacementAuthorization(
        original_tx_hash=source.tx_hash,
        replacement_tx_hash=replacement_tx_hash,
        intent_hash=assembly.intent.intent_hash(),
        authorization_hash=authorization_hash(assembly.authorization),
        nonce=source.nonce,
        old_max_fee_per_gas=source.max_fee_per_gas,
        old_max_priority_fee_per_gas=source.max_priority_fee_per_gas,
        new_max_fee_per_gas=max_fee_per_gas,
        new_max_priority_fee_per_gas=max_priority_fee_per_gas,
        policy_hash=replacement_policy.policy_hash(),
    )
    try:
        replacement_auth.validate(policy=replacement_policy)
    except ValueError as exc:
        raise ReplacementCoordinatorError(str(exc)) from exc

    try:
        unsigned_record = build_signed_record(
            assembly.intent,
            assembly.authorization,
            assembly.envelope,
            bound_record,
            replacement_tx_hash,
            now=now,
        )
        replacement_record = TransactionRecord(
            **{**unsigned_record.canonical(), "state": ExecutionState.SIGNED, "replacement_of": source.tx_hash}
        )
        replacement_record.validate_binding(
            assembly.intent,
            assembly.authorization,
            assembly.envelope,
            bound_record,
        )
    except Exception as exc:
        raise ReplacementCoordinatorError(str(exc)) from exc

    try:
        with store._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT record_hash,intent_hash,state,tx_hash,sender,nonce,reservation_id FROM transaction_records WHERE record_hash=?",
                (source.record_hash(),),
            ).fetchone()
            if row is None:
                raise ReplacementCoordinatorError("source transaction disappeared before replacement persistence")
            if row[1].lower() != source.intent_hash.lower() or row[3].lower() != source.tx_hash.lower():
                raise ReplacementCoordinatorError("source transaction identity changed before replacement persistence")
            if ExecutionState(row[2]) not in {ExecutionState.DROPPED, ExecutionState.REPLACED}:
                raise ReplacementCoordinatorError("source transaction is no longer replaceable")

            nrow = db.execute(
                "SELECT status,tx_hash,reservation_id,intent_hash FROM nonce_records WHERE sender=? AND nonce=?",
                (source.sender.lower(), source.nonce),
            ).fetchone()
            if nrow is None or nrow[2] != source.reservation_id or nrow[3].lower() != source.intent_hash.lower():
                raise ReplacementCoordinatorError("durable nonce identity changed before replacement persistence")
            if nrow[1] is not None and nrow[1].lower() != source.tx_hash.lower():
                raise ReplacementCoordinatorError("durable nonce active transaction changed before replacement persistence")
            if nrow[0] not in {NonceStatus.DROPPED.value, NonceStatus.REPLACED.value}:
                raise ReplacementCoordinatorError("durable nonce is no longer replaceable")
            if db.execute("SELECT 1 FROM transaction_records WHERE tx_hash=?", (replacement_tx_hash.lower(),)).fetchone():
                raise ReplacementCoordinatorError("replacement transaction hash is already recorded")

            payload = replacement_record.canonical()
            db.execute(
                "INSERT INTO transaction_records(record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    replacement_record.record_hash(), payload["intent_hash"], payload["authorization_hash"],
                    payload["reservation_id"], payload["chain_id"], payload["sender"], payload["executor"],
                    payload["nonce"], payload["calldata_hash"], payload["gas_limit"], payload["max_fee_per_gas"],
                    payload["max_priority_fee_per_gas"], payload["tx_hash"], payload["state"], payload["replacement_of"],
                ),
            )
            db.execute(
                "UPDATE nonce_records SET status=?,tx_hash=?,replacement_of=? WHERE sender=? AND nonce=?",
                (NonceStatus.SIGNED.value, replacement_tx_hash.lower(), source.tx_hash.lower(), source.sender.lower(), source.nonce),
            )
            db.execute("COMMIT")
    except Exception as exc:
        if isinstance(exc, ReplacementCoordinatorError):
            raise
        raise ReplacementCoordinatorError(str(exc)) from exc

    return PreparedReplacement(
        source=source,
        assembly=assembly,
        authority=executor_authority,
        preflight=preflight,
        governor=governor,
        bound_nonce=bound_record,
        signed_transaction=signed_transaction,
        transaction_record=replacement_record,
        replacement_authorization=replacement_auth,
    )
