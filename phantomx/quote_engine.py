"""Exact integer quote/economic primitives.

This layer intentionally accepts venue-specific quote callables. It does not
invent prices from spot reserves and never treats a forecast as settlement
truth. Each leg's integer output becomes the next leg's integer input.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Sequence

from .economics import CostBreakdown, strict_profit_ok


class QuoteEngineError(ValueError):
    pass


@dataclass(frozen=True)
class ExactQuote:
    venue: str
    token_in: str
    token_out: str
    amount_in: int
    amount_out: int
    block_number: int
    fee_raw: int = 0

    def __post_init__(self) -> None:
        if self.amount_in <= 0 or self.amount_out < 0:
            raise QuoteEngineError("quote amounts must be non-negative with positive input")
        if self.block_number < 0:
            raise QuoteEngineError("block number cannot be negative")
        if not self.venue or not self.token_in or not self.token_out:
            raise QuoteEngineError("quote identity fields are required")


@dataclass(frozen=True)
class SequentialRouteQuote:
    quotes: tuple[ExactQuote, ...]
    final_amount: int

    @property
    def initial_amount(self) -> int:
        return self.quotes[0].amount_in


def quote_v2_exact(
    venue: str,
    token_in: str,
    token_out: str,
    amount_in: int,
    block_number: int,
    get_amount_out: Callable[[int], int],
) -> ExactQuote:
    """Wrap an exact router/quoter result without floating-point conversion."""
    if amount_in <= 0:
        raise QuoteEngineError("amount_in must be positive")
    amount_out = int(get_amount_out(amount_in))
    if amount_out < 0:
        raise QuoteEngineError("negative quote output")
    return ExactQuote(venue, token_in, token_out, amount_in, amount_out, block_number)


def quote_sequential(
    legs: Sequence[tuple[str, str, str, Callable[[int], int]]],
    amount_in: int,
    block_number: int,
) -> SequentialRouteQuote:
    """Quote A→B→... exactly, propagating each integer output into the next leg."""
    if not legs:
        raise QuoteEngineError("route must contain at least one leg")
    if amount_in <= 0:
        raise QuoteEngineError("amount_in must be positive")
    current = amount_in
    quotes: list[ExactQuote] = []
    for venue, token_in, token_out, getter in legs:
        quote = quote_v2_exact(venue, token_in, token_out, current, block_number, getter)
        quotes.append(quote)
        current = quote.amount_out
        if current <= 0:
            raise QuoteEngineError("route terminated with zero output")
    return SequentialRouteQuote(tuple(quotes), current)


def net_profit_usd(
    final_settlement_usd: Decimal,
    flash_repayment_usd: Decimal,
    costs: CostBreakdown,
) -> Decimal:
    """Compute settlement net after every declared cost class."""
    return final_settlement_usd - flash_repayment_usd - costs.total


def profitable_after_costs(
    final_settlement_usd: Decimal,
    flash_repayment_usd: Decimal,
    costs: CostBreakdown,
) -> bool:
    return strict_profit_ok(net_profit_usd(final_settlement_usd, flash_repayment_usd, costs))
