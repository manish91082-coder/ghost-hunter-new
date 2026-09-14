"""Durable Phase-19 execution preparation coordinator.

This module is the narrow bridge from proven route/economic evidence into the
existing durable nonce, governor, signer and transaction-record boundaries.
It performs no RPC, relay submission or live broadcast.
"""
from __future__ import annotations

from dataclasses import dataclass
from secrets import token_hex

from .economic_proof import EconomicProof
from .execution import Authorization, ExecutionIntent, ExecutionState
from .execution_assembly import ExecutionAssembly, assemble_execution
from .evm_preflight import EVMPreflightResult, preflight_execution
from .governor import GovernorDecision, GovernorPolicy, govern_execution
from .nonce_binding import BoundNonce, bind_nonce
from .signer import SignedTransaction, TransactionSigner, sign_governed_transaction
from .sqlite_execution_store import SQLiteExecutionStore
from .transaction_record import TransactionRecord, build_signed_record
from .durable_nonce import DurableNonceInvariantError, DurableNonceRecord, NonceStatus


class ExecutionCoordinatorError(RuntimeError):
    """Raised when durable execution preparation cannot be completed safely."""


@dataclass(frozen=True)
class PreparedExecution:
    """Immutable evidence bundle persisted at the signer boundary."""

    reservation: DurableNonceRecord
    assembly: ExecutionAssembly
    preflight: EVMPreflightResult
    governor: GovernorDecision
    bound_nonce: BoundNonce
    signed_transaction: SignedTransaction
    transaction_record: TransactionRecord



def _new_reservation_id(intent_hint: str | None = None) -> str:
    prefix = intent_hint.strip() if isinstance(intent_hint, str) and intent_hint.strip() else "phase19"
    return f"{prefix}-res-{token_hex(16)}"


def prepare_signed_execution(
    *,
    store: SQLiteExecutionStore,
    simulation,
    economic_proof: EconomicProof,
    executor: str,
    sender: str,
    chain_pending_nonce: int,
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
    reservation_id: str | None = None,
) -> PreparedExecution:
    """Prepare, durably bind, govern, sign and persist one exact transaction.

    The nonce is allocated before the final intent is built, then the allocated
    reservation is atomically bound to that final intent hash. Any failure
    before signing releases the still-uncommitted reservation. After signing,
    persistence is mandatory and failures leave the reservation intact for
    forensic recovery rather than silently recycling the nonce.
    """
    if chain_pending_nonce < 0:
        raise ExecutionCoordinatorError("chain pending nonce cannot be negative")
    if now < 0 or current_block_number < 0:
        raise ExecutionCoordinatorError("time and block must be non-negative")

    reservation_id = reservation_id or _new_reservation_id()
    reservation = store.reserve_unbound_nonce(
        sender,
        reservation_id,
        chain_pending_nonce=chain_pending_nonce,
    )

    signed = False
    try:
        assembly = assemble_execution(
            simulation=simulation,
            economic_proof=economic_proof,
            executor=executor,
            sender=sender,
            nonce=reservation.nonce,
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

        store.bind_reserved_intent(
            sender=sender,
            nonce=reservation.nonce,
            reservation_id=reservation.reservation_id,
            intent_hash=assembly.intent_hash,
        )
        bound_record = store.get_nonce(sender, reservation.nonce)
        if bound_record.intent_hash.lower() != assembly.intent_hash.lower():
            raise ExecutionCoordinatorError("durable nonce intent binding did not persist")

        bound_nonce = bind_nonce(
            DurableNonceRecord(
                sender=bound_record.sender,
                nonce=bound_record.nonce,
                reservation_id=bound_record.reservation_id,
                intent_hash=bound_record.intent_hash,
                status=bound_record.status,
                tx_hash=bound_record.tx_hash,
                replacement_of=bound_record.replacement_of,
            ),
            assembly.intent,
            assembly.authorization,
        )

        preflight = preflight_execution(
            intent=assembly.intent,
            authorization=assembly.authorization,
            envelope=assembly.envelope,
            simulation=assembly.simulation,
            economic_proof=assembly.economic_proof,
            now=now,
        )

        governor = govern_execution(
            policy=policy,
            preflight=preflight,
            intent=assembly.intent,
            envelope=assembly.envelope,
            economic_proof=assembly.economic_proof,
            lifecycle_state=ExecutionState.VERIFIED,
            nonce_reserved=True,
            replay_consumed=False,
            current_block_number=current_block_number,
            now=now,
            ai_rank=ai_rank,
        )
        if not governor.approved:
            raise ExecutionCoordinatorError(f"governor blocked execution: {governor.reason}")

        signed_transaction = sign_governed_transaction(
            signer=signer,
            governor=governor,
            intent=assembly.intent,
            authorization=assembly.authorization,
            envelope=assembly.envelope,
            now=now,
        )
        signed = True

        transaction_record = build_signed_record(
            assembly.intent,
            assembly.authorization,
            assembly.envelope,
            bound_nonce,
            signed_transaction.transaction_hash,
            now=now,
        )
        persisted = store.create_signed_transaction(
            transaction_record,
            intent=assembly.intent,
            bound_nonce=bound_nonce,
        )
        return PreparedExecution(
            reservation=store.get_nonce(sender, reservation.nonce),
            assembly=assembly,
            preflight=preflight,
            governor=governor,
            bound_nonce=bound_nonce,
            signed_transaction=signed_transaction,
            transaction_record=persisted,
        )
    except Exception as exc:
        if not signed:
            try:
                store.release_reserved_nonce(
                    sender=sender,
                    nonce=reservation.nonce,
                    reservation_id=reservation.reservation_id,
                )
            except Exception as release_exc:
                raise ExecutionCoordinatorError(
                    f"execution preparation failed and reservation release also failed: {release_exc}"
                ) from exc
        if isinstance(exc, ExecutionCoordinatorError):
            raise
        if isinstance(exc, DurableNonceInvariantError):
            raise ExecutionCoordinatorError(str(exc)) from exc
        raise ExecutionCoordinatorError(str(exc)) from exc
