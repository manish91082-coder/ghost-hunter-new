"""On-chain native-token/USD valuation derived from exact USDC quotes.

The valuation source is an exact WPOL -> USDC quote snapshot at a pinned
Polygon block. No external price API or hardcoded POL/USD price is used.
The conservative gas valuation uses the highest independently observed
WPOL/USD quote from the same native amount and block because a higher native
USD price produces a higher USD-denominated gas cost bound.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable

from .quote_snapshot import QuoteSnapshot

class NativeValuationError(ValueError):
    """Raised when native/USD valuation evidence is unsafe or incomplete."""

@dataclass(frozen=True)
class NativeUSDObservation:
    chain_id: int
    block_number: int
    native_token: str
    stable_token: str
    native_amount_raw: int
    stable_amount_raw: int
    price_usd: Decimal
    source_quote_hash: str

    def __post_init__(self) -> None:
        if self.chain_id != 137 or self.block_number < 0:
            raise NativeValuationError("valuation must be Polygon and block-bound")
        if self.native_amount_raw <= 0 or self.stable_amount_raw <= 0:
            raise NativeValuationError("valuation amounts must be positive")
        if not self.native_token or not self.stable_token:
            raise NativeValuationError("valuation token identities are required")
        if not isinstance(self.price_usd, Decimal) or not self.price_usd.is_finite() or self.price_usd <= 0:
            raise NativeValuationError("price_usd must be finite and positive")
        if not isinstance(self.source_quote_hash, str) or len(self.source_quote_hash) != 66 or not self.source_quote_hash.startswith("0x"):
            raise NativeValuationError("source_quote_hash must be a 32-byte hash")

def observation_from_quote(quote: QuoteSnapshot, *, native_token: str, stable_token: str) -> NativeUSDObservation:
    if quote.token_in.lower() != native_token.lower() or quote.token_out.lower() != stable_token.lower():
        raise NativeValuationError("quote is not a native->stable valuation quote")
    if quote.amount_in <= 0 or quote.amount_out <= 0:
        raise NativeValuationError("quote amounts must be positive")
    try:
        price = (Decimal(quote.amount_out) / Decimal(10**6)) / (Decimal(quote.amount_in) / Decimal(10**18))
    except (InvalidOperation, ZeroDivisionError) as exc:
        raise NativeValuationError("cannot derive native/USD price") from exc
    return NativeUSDObservation(
        chain_id=quote.chain_id, block_number=quote.block_number,
        native_token=native_token, stable_token=stable_token,
        native_amount_raw=quote.amount_in, stable_amount_raw=quote.amount_out,
        price_usd=price, source_quote_hash=quote.quote_hash.lower(),
    )

@dataclass(frozen=True)
class ConservativeNativeValuation:
    chain_id: int
    block_number: int
    native_token: str
    stable_token: str
    native_amount_raw: int
    conservative_price_usd: Decimal
    evidence_hashes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.chain_id != 137:
            raise NativeValuationError("valuation must be Polygon mainnet")
        if self.block_number < 0 or self.native_amount_raw <= 0:
            raise NativeValuationError("valuation block/amount is invalid")
        if not self.evidence_hashes:
            raise NativeValuationError("valuation requires quote evidence")

def build_conservative_native_valuation(observations: Iterable[NativeUSDObservation]) -> ConservativeNativeValuation:
    items = tuple(observations)
    if not items:
        raise NativeValuationError("at least one valuation observation is required")
    first = items[0]
    if any(
        item.chain_id != first.chain_id
        or item.block_number != first.block_number
        or item.native_token.lower() != first.native_token.lower()
        or item.stable_token.lower() != first.stable_token.lower()
        or item.native_amount_raw != first.native_amount_raw
        for item in items
    ):
        raise NativeValuationError("valuation observations must share chain, block and native amount")
    chosen = max(items, key=lambda item: item.price_usd)
    hashes = tuple(sorted({item.source_quote_hash.lower() for item in items}))
    return ConservativeNativeValuation(
        chain_id=first.chain_id, block_number=first.block_number,
        native_token=first.native_token, stable_token=first.stable_token,
        native_amount_raw=first.native_amount_raw,
        conservative_price_usd=chosen.price_usd, evidence_hashes=hashes,
    )
