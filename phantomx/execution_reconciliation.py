"""Durable realized-settlement reconciliation for Phase 19.

This boundary accepts only a canonical successful receipt plus independently
measured settlement accounting. It never treats expected PnL as realized PnL.
The settlement evidence and terminal execution state are committed together.
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
    final_settlement: Decimal
    flash_repayment: Decimal
    costs: CostBreakdown
    realized_net_profit_usd: Decimal
    profit_confirmed: bool

    def canonical(self) -> dict[str, object]:
        return {
            "record_hash": self.record_hash.lower(),
            "tx_hash": self.tx_hash.lower(),
            "receipt": {
                "tx_hash": self.receipt.tx_hash.lower(),
                "status": self.receipt.status,
                "gas_used": self.receipt.gas_used,
                "effective_gas_price": self.receipt.effective_gas_price,
                "block_number": self.receipt.block_number,
            },
            "final_settlement": str(self.final_settlement),
            "flash_repayment": str(self.flash_repayment),
            "costs": {
                "flash_loan_fee": str(self.costs.flash_loan_fee),
                "dex_fees": str(self.costs.dex_fees),
                "price_impact": str(self.costs.price_impact),
                "gas": str(self.costs.gas),
                "relay": str(self.costs.relay),
                "other": str(self.costs.other),
            },
            "realized_net_profit_usd": str(self.realized_net_profit_usd),
            "profit_confirmed": self.profit_confirmed,
        }

    def evidence_hash(self) -> str:
        payload = self.canonical().copy()
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
    """Persist realized settlement and terminal profit state atomically.

    The transaction must already be durably INCLUDED. The chain observation must
    prove the exact tx is included in the canonical chain. Gas is charged from
    receipt gasUsed * effectiveGasPrice after its USD conversion is supplied in
    ``costs.gas``. Profit confirmation uses the strict > $0.20 invariant.
    """
    if observation.state is not ChainObservationState.INCLUDED:
        raise ExecutionReconciliationError("settlement requires canonical INCLUDED observation")
    if not _TX_HASH.fullmatch(observation.tx_hash) or not _TX_HASH.fullmatch(receipt.tx_hash):
        raise ExecutionReconciliationError("invalid transaction hash")
    if observation.tx_hash.lower() != receipt.tx_hash.lower():
        raise ExecutionReconciliationError("observation and receipt transaction hash mismatch")
    if receipt.status != 1:
        raise ExecutionReconciliationError("realized settlement requires successful receipt")
    if receipt.gas_used < 0 or receipt.effective_gas_price < 0 or receipt.block_number < 0:
        raise ExecutionReconciliationError("invalid receipt accounting fields")

    final_settlement_d = _decimal(final_settlement, "final_settlement")
    flash_repayment_d = _decimal(flash_repayment, "flash_repayment")
    costs_d = CostBreakdown(
        flash_loan_fee=_decimal(costs.flash_loan_fee, "flash_loan_fee"),
        dex_fees=_decimal(costs.dex_fees, "dex_fees"),
        price_impact=_decimal(costs.price_impact, "price_impact"),
        gas=_decimal(costs.gas, "gas"),
        relay=_decimal(costs.relay, "relay"),
        other=_decimal(costs.other, "other"),
    )
    result = reconcile(
        receipt=receipt,
        final_settlement=final_settlement_d,
        flash_repayment=flash_repayment_d,
        costs=costs_d,
    )
    tx = store.get_transaction(next_hash for next_hash in []) if False else None
    # The record is identified by the intent hash; transaction lookup below is
    # deliberately direct so the caller cannot supply an unrelated tx record.
    with store._connect() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of FROM transaction_records WHERE intent_hash=?",
                (intent.intent_hash().lower(),),
            ).fetchone()
            if row is None:
                raise ExecutionReconciliationError("unknown durable transaction for execution intent")
            if row[12].lower() != receipt.tx_hash.lower():
                raise ExecutionReconciliationError("receipt does not match durable transaction")
            current_state = ExecutionState(row[13])
            if current_state is not ExecutionState.INCLUDED:
                raise ExecutionReconciliationError(f"transaction must be INCLUDED before settlement, got {current_state.value}")

            record_hash = str(row[0])
            settlement_payload = {
                "tx_hash": receipt.tx_hash.lower(),
                "receipt": {
                    "status": receipt.status,
                    "gas_used": receipt.gas_used,
                    "effective_gas_price": receipt.effective_gas_price,
                    "block_number": receipt.block_number,
                },
                "final_settlement": str(final_settlement_d),
                "flash_repayment": str(flash_repayment_d),
                "costs": {
                    "flash_loan_fee": str(costs_d.flash_loan_fee),
                    "dex_fees": str(costs_d.dex_fees),
                    "price_impact": str(costs_d.price_impact),
                    "gas": str(costs_d.gas),
                    "relay": str(costs_d.relay),
                    "other": str(costs_d.other),
                },
                "realized_net_profit_usd": str(result.settlement.realized_net_profit),
                "profit_confirmed": result.profit_confirmed,
            }
            evidence_hash = keccak256_hex(json.dumps(settlement_payload, sort_keys=True, separators=(",", ":")).encode())
            settlement_record_hash = keccak256_hex(json.dumps({"transaction_record_hash": record_hash.lower(), "evidence_hash": evidence_hash}, sort_keys=True, separators=(",", ":")).encode())

            existing = db.execute(
                "SELECT record_hash,evidence_hash FROM settlement_records WHERE transaction_record_hash=?",
                (record_hash.lower(),),
            ).fetchone()
            if existing is not None:
                if existing[1].lower() != evidence_hash.lower():
                    raise ExecutionReconciliationError("conflicting settlement evidence already exists")
                db.execute("COMMIT")
            else:
                db.execute(
                    "INSERT INTO settlement_records(record_hash,transaction_record_hash,tx_hash,status,gas_used,effective_gas_price,block_number,final_settlement,flash_repayment,flash_loan_fee,dex_fees,price_impact,gas,relay,other,realized_net_profit_usd,profit_confirmed,evidence_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        settlement_record_hash,
                        record_hash.lower(),
                        receipt.tx_hash.lower(),
                        receipt.status,
                        receipt.gas_used,
                        receipt.effective_gas_price,
                        receipt.block_number,
                        str(final_settlement_d),
                        str(flash_repayment_d),
                        str(costs_d.flash_loan_fee),
                        str(costs_d.dex_fees),
                        str(costs_d.price_impact),
                        str(costs_d.gas),
                        str(costs_d.relay),
                        str(costs_d.other),
                        str(result.settlement.realized_net_profit),
                        1 if result.profit_confirmed else 0,
                        evidence_hash,
                    ),
                )
                db.execute("UPDATE transaction_records SET state=? WHERE record_hash=? AND state=?", (ExecutionState.PROFIT_CONFIRMED.value if result.profit_confirmed else ExecutionState.PROFIT_FAILED.value, record_hash.lower(), ExecutionState.INCLUDED.value))
                db.execute("COMMIT")
        except Exception:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise

    stored = store.get_transaction(record_hash)
    with store._connect() as db:
        row = db.execute("SELECT record_hash,transaction_record_hash,tx_hash,status,gas_used,effective_gas_price,block_number,final_settlement,flash_repayment,flash_loan_fee,dex_fees,price_impact,gas,relay,other,realized_net_profit_usd,profit_confirmed FROM settlement_records WHERE transaction_record_hash=?", (record_hash.lower(),)).fetchone()
    if row is None:
        raise ExecutionReconciliationError("settlement record disappeared after commit")
    settlement_record = DurableSettlementRecord(
        record_hash=row[0],
        tx_hash=row[2],
        receipt=ReceiptRecord(tx_hash=row[2], status=int(row[3]), gas_used=int(row[4]), effective_gas_price=int(row[5]), block_number=int(row[6])),
        final_settlement=Decimal(row[7]),
        flash_repayment=Decimal(row[8]),
        costs=CostBreakdown(flash_loan_fee=Decimal(row[9]), dex_fees=Decimal(row[10]), price_impact=Decimal(row[11]), gas=Decimal(row[12]), relay=Decimal(row[13]), other=Decimal(row[14])),
        realized_net_profit_usd=Decimal(row[15]),
        profit_confirmed=bool(row[16]),
    )
    if settlement_record.evidence_hash().lower() != keccak256_hex(json.dumps({"tx_hash": settlement_record.tx_hash.lower(), "receipt": {"status": settlement_record.receipt.status, "gas_used": settlement_record.receipt.gas_used, "effective_gas_price": settlement_record.receipt.effective_gas_price, "block_number": settlement_record.receipt.block_number}, "final_settlement": str(settlement_record.final_settlement), "flash_repayment": str(settlement_record.flash_repayment), "costs": {"flash_loan_fee": str(settlement_record.costs.flash_loan_fee), "dex_fees": str(settlement_record.costs.dex_fees), "price_impact": str(settlement_record.costs.price_impact), "gas": str(settlement_record.costs.gas), "relay": str(settlement_record.costs.relay), "other": str(settlement_record.costs.other)}, "realized_net_profit_usd": str(settlement_record.realized_net_profit_usd), "profit_confirmed": settlement_record.profit_confirmed}, sort_keys=True, separators=(",", ":")).encode()).lower():
        raise ExecutionReconciliationError("stored settlement evidence hash mismatch")
    return ReconciledExecution(
        transaction_record_hash=record_hash,
        settlement_record=settlement_record,
        reconciliation=result,
        transaction_state=stored.state,
    )
