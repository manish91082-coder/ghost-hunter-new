"""Small, dependency-free economic primitives for the canonical execution spine.

This module intentionally contains no RPC, Web3, AI, or signing code.  It is a
pure policy layer so the most important economic invariant can be tested in
isolation and reused by later execution components.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

USD = Decimal
STRICT_MIN_NET_PROFIT_USD = USD("0.20")


def strict_profit_ok(realized_net_profit_usd: Decimal) -> bool:
    """Return True only when realized net profit is strictly greater than $0.20."""
    return USD(realized_net_profit_usd) > STRICT_MIN_NET_PROFIT_USD


@dataclass(frozen=True)
class CostBreakdown:
    """All costs are USD-equivalent and must be transaction attributable."""

    flash_loan_fee: Decimal = USD("0")
    dex_fees: Decimal = USD("0")
    price_impact: Decimal = USD("0")
    gas: Decimal = USD("0")
    relay: Decimal = USD("0")
    other: Decimal = USD("0")

    @property
    def total(self) -> Decimal:
        return sum(
            (
                self.flash_loan_fee,
                self.dex_fees,
                self.price_impact,
                self.gas,
                self.relay,
                self.other,
            ),
            USD("0"),
        )


@dataclass(frozen=True)
class RealizedSettlement:
    """Settlement values after the transaction has been observed on-chain."""

    final_settlement: Decimal
    flash_repayment: Decimal
    costs: CostBreakdown

    @property
    def gross_surplus(self) -> Decimal:
        return self.final_settlement - self.flash_repayment

    @property
    def realized_net_profit(self) -> Decimal:
        return self.gross_surplus - self.costs.total

    @property
    def profit_confirmed(self) -> bool:
        return strict_profit_ok(self.realized_net_profit)
