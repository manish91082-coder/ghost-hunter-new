"""Dependency-free receipt/realized-PnL models for Phase 19 tests."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .economics import CostBreakdown, RealizedSettlement


@dataclass(frozen=True)
class ReceiptRecord:
    tx_hash: str
    status: int
    gas_used: int
    effective_gas_price: int
    block_number: int

    @property
    def gas_cost_wei(self) -> int:
        return self.gas_used * self.effective_gas_price


@dataclass(frozen=True)
class Reconciliation:
    receipt: ReceiptRecord
    settlement: RealizedSettlement

    @property
    def successful(self) -> bool:
        return self.receipt.status == 1

    @property
    def profit_confirmed(self) -> bool:
        return self.successful and self.settlement.profit_confirmed


def reconcile(
    *,
    receipt: ReceiptRecord,
    final_settlement: Decimal,
    flash_repayment: Decimal,
    costs: CostBreakdown,
) -> Reconciliation:
    """Build realized accounting from receipt + independently measured settlement.

    The receipt's gas fields are evidence. Callers must convert gas cost into the
    settlement currency before constructing CostBreakdown.gas.
    """
    return Reconciliation(
        receipt=receipt,
        settlement=RealizedSettlement(
            final_settlement=final_settlement,
            flash_repayment=flash_repayment,
            costs=costs,
        ),
    )
