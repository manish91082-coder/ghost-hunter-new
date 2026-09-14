"""Durable realized-settlement reconciliation for Phase 19.

Only a canonical successful receipt plus independently measured settlement can
reach the terminal profit states. Expected PnL is never treated as realized.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import re

from .chain_observer import ChainObservationState, ObservationDecision
from .economics import CostBreakdown
from .execution import ExecutionIntent, ExecutionState
from .hashing import keccak256_hex
from .settlement import ReceiptRecord, Reconciliation, reconcile
from .sqlite_execution_store import SQLiteExecutionStore

_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")


class ExecutionReconciliationError(ValueError):
    """Raised when realized settlement evidence cannot be safely committed."""


@dataclass(frozen=True)
class DurableSettlementRecord:
    record_hash: str
    tx_hash: str
    receipt: ReceiptRecord
    block_hash: str
    canonical_block_hash: str
    final_settlement: Decimal
    flash_repayment: Decimal
    costs: CostBreakdown
    realized_net_profit_usd: Decimal
    profit_confirmed: bool

    def canonical(self) -> dict[str, object]:
        return _evidence_payload(
            tx_hash=self.tx_hash,
            receipt=self.receipt,
            block_hash=self.block_hash,
            canonical_block_hash=self.canonical_block_hash,
            final_settlement=self.final_settlement,
            flash_repayment=self.flash_repayment,
            costs=self.costs,
            realized_net_profit_usd=self.realized_net_profit_usd,
            profit_confirmed=self.profit_confirmed,
            record_hash=self.record_hash,
        )

    def evidence_hash(self) -> str:
        payload = self.canonical()
        payload.pop("record_hash")
        return keccak256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


@dataclass(frozen=True)
class ReconciledExecution:
    transaction_record_hash: str
    settlement_record: DurableSettlementRecord
    reconciliation: Reconciliation
    transaction_state: ExecutionState


def _decimal(value: Decimal | str | int | float, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ExecutionReconciliationError(f"invalid {field}") from exc
    if not result.is_finite():
        raise ExecutionReconciliationError(f"{field} must be finite")
    return result


def _ensure_schema(store: SQLiteExecutionStore) -> None:
    with store._connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS settlement_records(
                record_hash TEXT PRIMARY KEY,
                transaction_record_hash TEXT NOT NULL UNIQUE,
                tx_hash TEXT NOT NULL,
                status INTEGER NOT NULL CHECK(status=1),
                gas_used INTEGER NOT NULL CHECK(gas_used>=0),
                effective_gas_price INTEGER NOT NULL CHECK(effective_gas_price>=0),
                block_number INTEGER NOT NULL CHECK(block_number>=0),
                block_hash TEXT NOT NULL,
                canonical_block_hash TEXT NOT NULL,
                final_settlement TEXT NOT NULL,
                flash_repayment TEXT NOT NULL,
                flash_loan_fee TEXT NOT NULL,
                dex_fees TEXT NOT NULL,
                price_impact TEXT NOT NULL,
                gas TEXT NOT NULL,
                relay TEXT NOT NULL,
                other TEXT NOT NULL,
                realized_net_profit_usd TEXT NOT NULL,
                profit_confirmed INTEGER NOT NULL CHECK(profit_confirmed IN(0,1)),
                evidence_hash TEXT NOT NULL
            )"""
        )


def _evidence_payload(
    *,
    tx_hash: str,
    receipt: ReceiptRecord,
    block_hash: str,
    canonical_block_hash: str,
    final_settlement: Decimal,
    flash_repayment: Decimal,
    costs: CostBreakdown,
    realized_net_profit_usd: Decimal,
    profit_confirmed: bool,
    record_hash: str,
) -> dict[str, object]:
    return {
        "record_hash": record_hash.lower(),
        "tx_hash": tx_hash.lower(),
        "receipt": {
            "tx_hash": receipt.tx_hash.lower(),
            "status": receipt.status,
            "gas_used": receipt.gas_used,
            "effective_gas_price": receipt.effective_gas_price,
            "block_number": receipt.block_number,
        },
        "block_hash": block_hash.lower(),
        "canonical_block_hash": canonical_block_hash.lower(),
        "final_settlement": str(final_settlement),
        "flash_repayment": str(flash_repayment),
        "costs": {
            "flash_loan_fee": str(costs.flash_loan_fee),
            "dex_fees": str(costs.dex_fees),
            "price_impact": str(costs.price_impact),
            "gas": str(costs.gas),
            "relay": str(costs.relay),
            "other": str(costs.other),
        },
        "realized_net_profit_usd": str(realized_net_profit_usd),
        "profit_confirmed": profit_confirmed,
    }


def _make_settlement_record(
    *,
    record_hash: str,
    receipt: ReceiptRecord,
    block_hash: str,
    canonical_block_hash: str,
    final_settlement: Decimal,
    flash_repayment: Decimal,
    costs: CostBreakdown,
    reconciliation: Reconciliation,
    evidence_hash: str,
) -> DurableSettlementRecord:
    return DurableSettlementRecord(
        record_hash=record_hash,
        tx_hash=receipt.tx_hash,
        receipt=receipt,
        block_hash=block_hash,
        canonical_block_hash=canonical_block_hash,
        final_settlement=final_settlement,
        flash_repayment=flash_repayment,
        costs=costs,
        realized_net_profit_usd=reconciliation.settlement.realized_net_profit,
        profit_confirmed=reconciliation.profit_confirmed,
    )


def _load_settlement(store: SQLiteExecutionStore, transaction_record_hash: str) -> DurableSettlementRecord:
    with store._connect() as db:
        row = db.execute(
            "SELECT record_hash,tx_hash,status,gas_used,effective_gas_price,block_number,block_hash,canonical_block_hash,final_settlement,flash_repayment,flash_loan_fee,dex_fees,price_impact,gas,relay,other,realized_net_profit_usd,profit_confirmed,evidence_hash FROM settlement_records WHERE transaction_record_hash=?",
            (transaction_record_hash.lower(),),
        ).fetchone()
    if row is None:
        raise ExecutionReconciliationError("durable settlement record is missing")
    record = DurableSettlementRecord(
        record_hash=row[0],
        tx_hash=row[1],
        receipt=ReceiptRecord(tx_hash=row[1], status=int(row[2]), gas_used=int(row[3]), effective_gas_price=int(row[4]), block_number=int(row[5])),
        block_hash=row[6],
        canonical_block_hash=row[7],
        final_settlement=Decimal(row[8]),
        flash_repayment=Decimal(row[9]),
        costs=CostBreakdown(flash_loan_fee=Decimal(row[10]), dex_fees=Decimal(row[11]), price_impact=Decimal(row[12]), gas=Decimal(row[13]), relay=Decimal(row[14]), other=Decimal(row[15])),
        realized_net_profit_usd=Decimal(row[16]),
        profit_confirmed=bool(row[17]),
    )
    if record.evidence_hash().lower() != str(row[18]).lower():
        raise ExecutionReconciliationError("stored settlement evidence hash mismatch")
    return record


def reconcile_included_execution(
    *,
    store: SQLiteExecutionStore,
    intent: ExecutionIntent,
    observation: ObservationDecision,
    receipt: ReceiptRecord,
    final_settlement: Decimal | str | int | float,
    flash_repayment: Decimal | str | int | float,
    costs: CostBreakdown,
) -> ReconciledExecution:
    """Atomically persist realized settlement and terminal profit state.

    ``costs.gas`` must be the USD conversion of receipt.gasUsed multiplied by
    receipt.effectiveGasPrice. The strict profit floor remains ``> $0.20``.
    """
    _ensure_schema(store)
    if observation.state is not ChainObservationState.INCLUDED:
        raise ExecutionReconciliationError("settlement requires canonical INCLUDED observation")
    if not _TX_HASH.fullmatch(observation.tx_hash) or not _TX_HASH.fullmatch(receipt.tx_hash):
        raise ExecutionReconciliationError("invalid transaction hash")
    if observation.tx_hash.lower() != receipt.tx_hash.lower():
        raise ExecutionReconciliationError("observation and receipt transaction hash mismatch")
    if receipt.status != 1:
        raise ExecutionReconciliationError("realized settlement requires successful receipt")
    if not observation.block_hash or not observation.canonical_block_hash:
        raise ExecutionReconciliationError("included settlement requires canonical block identity")
    if observation.block_hash.lower() != observation.canonical_block_hash.lower():
        raise ExecutionReconciliationError("settlement block is not canonical")
    if receipt.gas_used < 0 or receipt.effective_gas_price < 0 or receipt.block_number < 0:
        raise ExecutionReconciliationError("invalid receipt accounting fields")

    final_settlement_d = _decimal(final_settlement, "final_settlement")
    flash_repayment_d = _decimal(flash_repayment, "flash_repayment")
    if final_settlement_d < 0 or flash_repayment_d < 0:
        raise ExecutionReconciliationError("settlement values cannot be negative")
    costs_d = CostBreakdown(
        flash_loan_fee=_decimal(costs.flash_loan_fee, "flash_loan_fee"),
        dex_fees=_decimal(costs.dex_fees, "dex_fees"),
        price_impact=_decimal(costs.price_impact, "price_impact"),
        gas=_decimal(costs.gas, "gas"),
        relay=_decimal(costs.relay, "relay"),
        other=_decimal(costs.other, "other"),
    )
    if min(costs_d.flash_loan_fee, costs_d.dex_fees, costs_d.price_impact, costs_d.gas, costs_d.relay, costs_d.other) < 0:
        raise ExecutionReconciliationError("cost components cannot be negative")

    reconciliation = reconcile(
        receipt=receipt,
        final_settlement=final_settlement_d,
        flash_repayment=flash_repayment_d,
        costs=costs_d,
    )
    with store._connect() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT record_hash,intent_hash,tx_hash,state FROM transaction_records WHERE intent_hash=?",
                (intent.intent_hash().lower(),),
            ).fetchone()
            if row is None:
                raise ExecutionReconciliationError("unknown durable transaction for execution intent")
            if row[2].lower() != receipt.tx_hash.lower():
                raise ExecutionReconciliationError("receipt does not match durable transaction")
            if ExecutionState(row[3]) is not ExecutionState.INCLUDED:
                raise ExecutionReconciliationError(f"transaction must be INCLUDED before settlement, got {row[3]}")

            record_hash = str(row[0])
            payload = _evidence_payload(
                tx_hash=receipt.tx_hash,
                receipt=receipt,
                block_hash=observation.block_hash,
                canonical_block_hash=observation.canonical_block_hash,
                final_settlement=final_settlement_d,
                flash_repayment=flash_repayment_d,
                costs=costs_d,
                realized_net_profit_usd=reconciliation.settlement.realized_net_profit,
                profit_confirmed=reconciliation.profit_confirmed,
                record_hash="0x" + "00" * 32,
            )
            payload.pop("record_hash")
            evidence_hash = keccak256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
            settlement_record_hash = keccak256_hex(json.dumps({"transaction_record_hash": record_hash.lower(), "evidence_hash": evidence_hash}, sort_keys=True, separators=(",", ":")).encode())

            existing = db.execute(
                "SELECT record_hash,evidence_hash FROM settlement_records WHERE transaction_record_hash=?",
                (record_hash.lower(),),
            ).fetchone()
            if existing is not None:
                if str(existing[1]).lower() != evidence_hash.lower():
                    raise ExecutionReconciliationError("conflicting settlement evidence already exists")
                db.execute("COMMIT")
            else:
                db.execute(
                    "INSERT INTO settlement_records(record_hash,transaction_record_hash,tx_hash,status,gas_used,effective_gas_price,block_number,block_hash,canonical_block_hash,final_settlement,flash_repayment,flash_loan_fee,dex_fees,price_impact,gas,relay,other,realized_net_profit_usd,profit_confirmed,evidence_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        settlement_record_hash,
                        record_hash.lower(),
                        receipt.tx_hash.lower(),
                        receipt.status,
                        receipt.gas_used,
                        receipt.effective_gas_price,
                        receipt.block_number,
                        observation.block_hash.lower(),
                        observation.canonical_block_hash.lower(),
                        str(final_settlement_d),
                        str(flash_repayment_d),
                        str(costs_d.flash_loan_fee),
                        str(costs_d.dex_fees),
                        str(costs_d.price_impact),
                        str(costs_d.gas),
                        str(costs_d.relay),
                        str(costs_d.other),
                        str(reconciliation.settlement.realized_net_profit),
                        1 if reconciliation.profit_confirmed else 0,
                        evidence_hash,
                    ),
                )
                terminal = ExecutionState.PROFIT_CONFIRMED if reconciliation.profit_confirmed else ExecutionState.PROFIT_FAILED
                db.execute("UPDATE transaction_records SET state=? WHERE record_hash=? AND state=?", (terminal.value, record_hash.lower(), ExecutionState.INCLUDED.value))
                db.execute("COMMIT")
        except Exception:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise

    stored = store.get_transaction(record_hash)
    settlement_record = _load_settlement(store, record_hash)
    return ReconciledExecution(
        transaction_record_hash=record_hash,
        settlement_record=settlement_record,
        reconciliation=reconciliation,
        transaction_state=stored.state,
    )
