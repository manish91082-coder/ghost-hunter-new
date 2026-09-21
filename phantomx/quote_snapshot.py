"""Canonical, hashable market-quote evidence for PhantomX.

A venue adapter may discover a quote, but execution must bind to an immutable
snapshot containing chain/block identity, exact integer amounts, venue target,
and observation time. Forecasts and reconstructed spot prices are deliberately
outside this contract.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from .hashing import keccak256_hex
from .quote_engine import ExactQuote, QuoteEngineError


class QuoteSnapshotError(QuoteEngineError):
    """Raised when quote evidence is incomplete or internally inconsistent."""


def _canonical_bytes(fields: dict[str, object]) -> bytes:
    return json.dumps(
        fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


@dataclass(frozen=True)
class QuoteSnapshot:
    schema_version: int
    chain_id: int
    block_number: int
    observed_at_unix: int
    dex: str
    pool_or_router: str
    token_in: str
    token_out: str
    amount_in: int
    amount_out: int
    fee_raw: int
    gas_estimate: Optional[int]
    quote_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QuoteSnapshotError("unsupported quote snapshot schema")
        if self.chain_id <= 0 or self.block_number < 0 or self.observed_at_unix < 0:
            raise QuoteSnapshotError("invalid chain/block/timestamp evidence")
        if not self.dex or not self.pool_or_router or not self.token_in or not self.token_out:
            raise QuoteSnapshotError("quote identity fields are required")
        if self.amount_in <= 0 or self.amount_out <= 0:
            raise QuoteSnapshotError("quote amounts must be positive")
        if self.fee_raw < 0:
            raise QuoteSnapshotError("fee_raw cannot be negative")
        if self.gas_estimate is not None and self.gas_estimate <= 0:
            raise QuoteSnapshotError("gas_estimate must be positive when present")
        if not self.quote_hash.startswith("0x") or len(self.quote_hash) != 66:
            raise QuoteSnapshotError("quote_hash must be a 32-byte 0x-prefixed digest")
        if self.quote_hash != self.compute_hash():
            raise QuoteSnapshotError("quote_hash does not match canonical snapshot fields")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "chain_id": self.chain_id,
            "block_number": self.block_number,
            "observed_at_unix": self.observed_at_unix,
            "dex": self.dex,
            "pool_or_router": self.pool_or_router,
            "token_in": self.token_in,
            "token_out": self.token_out,
            "amount_in": self.amount_in,
            "amount_out": self.amount_out,
            "fee_raw": self.fee_raw,
            "gas_estimate": self.gas_estimate,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.canonical_dict())

    def compute_hash(self) -> str:
        return keccak256_hex(self.canonical_bytes())

    @classmethod
    def from_exact_quote(
        cls,
        quote: ExactQuote,
        *,
        chain_id: int,
        observed_at_unix: int,
        pool_or_router: str,
        gas_estimate: Optional[int] = None,
    ) -> "QuoteSnapshot":
        if not pool_or_router:
            raise QuoteSnapshotError("pool_or_router is required")
        fields: dict[str, object] = {
            "schema_version": 1,
            "chain_id": chain_id,
            "block_number": quote.block_number,
            "observed_at_unix": observed_at_unix,
            "dex": quote.venue,
            "pool_or_router": pool_or_router,
            "token_in": quote.token_in,
            "token_out": quote.token_out,
            "amount_in": quote.amount_in,
            "amount_out": quote.amount_out,
            "fee_raw": quote.fee_raw,
            "gas_estimate": gas_estimate,
        }
        quote_hash = keccak256_hex(_canonical_bytes(fields))
        return cls(**fields, quote_hash=quote_hash)
