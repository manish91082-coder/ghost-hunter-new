"""Deterministic, hash-bound candidate economic proof for Phase-19.

This module is deliberately pure. It does not fetch prices, estimate gas, call
an RPC, sign, submit, or claim realized profit. Upstream components must supply
explicit valuation and worst-case cost evidence. The resulting proof is safe
to bind into ExecutionIntent/Authorization and is distinct from post-receipt
realized settlement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable

from .economics import CostBreakdown, STRICT_MIN_NET_PROFIT_USD
from .hashing import keccak256_hex


class EconomicProofError(ValueError):
    """Raised when an economic proof cannot be constructed safely."""


def _decimal(value: Decimal | int | str, name: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise EconomicProofError(f"{name} is not a valid decimal") from exc
    if not parsed.is_finite():
        raise EconomicProofError(f"{name} must be finite")
    if parsed < 0:
        raise EconomicProofError(f"{name} cannot be negative")
    return parsed


def _hash(value: str, name: str) -> str:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise EconomicProofError(f"{name} must be a 32-byte 0x hash")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise EconomicProofError(f"{name} must be hexadecimal") from exc
    return value.lower()


@dataclass(frozen=True)
class EconomicProof:
    """Worst-case candidate economics bound to route/quote/valuation evidence.

    ``loan_principal_usd`` excludes the flash-loan fee. The fee is represented
    exactly once by ``costs.flash_loan_fee``.
    """

    schema_version: int
    route_hash: str
    quote_hashes: tuple[str, ...]
    valuation_hash: str
    final_settlement_usd: Decimal
    loan_principal_usd: Decimal
    costs: CostBreakdown
    max_gas_usd: Decimal
    max_relay_usd: Decimal
    minimum_net_profit_usd: Decimal = STRICT_MIN_NET_PROFIT_USD
    proof_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise EconomicProofError("unsupported economic proof schema")
        object.__setattr__(self, "route_hash", _hash(self.route_hash, "route_hash"))
        object.__setattr__(self, "valuation_hash", _hash(self.valuation_hash, "valuation_hash"))
        hashes = tuple(_hash(item, "quote_hash") for item in self.quote_hashes)
        if not hashes:
            raise EconomicProofError("at least one quote hash is required")
        object.__setattr__(self, "quote_hashes", hashes)

        for name in (
            "final_settlement_usd",
            "loan_principal_usd",
            "max_gas_usd",
            "max_relay_usd",
            "minimum_net_profit_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))

        normalized_costs = {
            field: _decimal(getattr(self.costs, field), f"costs.{field}")
            for field in (
                "flash_loan_fee",
                "dex_fees",
                "price_impact",
                "gas",
                "relay",
                "other",
            )
        }
        object.__setattr__(self, "costs", CostBreakdown(**normalized_costs))

        if self.costs.gas > self.max_gas_usd:
            raise EconomicProofError("gas cost exceeds authorized maximum")
        if self.costs.relay > self.max_relay_usd:
            raise EconomicProofError("relay cost exceeds authorized maximum")
        if self.minimum_net_profit_usd <= 0:
            raise EconomicProofError("minimum net profit must be positive")

        expected = self._digest()
        if self.proof_hash:
            if self.proof_hash.lower() != expected:
                raise EconomicProofError("economic proof hash mismatch")
            object.__setattr__(self, "proof_hash", self.proof_hash.lower())
        else:
            object.__setattr__(self, "proof_hash", expected)

    @property
    def gross_surplus_usd(self) -> Decimal:
        return self.final_settlement_usd - self.loan_principal_usd

    @property
    def total_cost_usd(self) -> Decimal:
        return self.costs.total

    @property
    def worst_case_net_profit_usd(self) -> Decimal:
        return self.gross_surplus_usd - self.total_cost_usd

    @property
    def economically_valid(self) -> bool:
        return self.worst_case_net_profit_usd > self.minimum_net_profit_usd

    def _canonical_payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "route_hash": self.route_hash,
            "quote_hashes": list(self.quote_hashes),
            "valuation_hash": self.valuation_hash,
            "final_settlement_usd": str(self.final_settlement_usd),
            "loan_principal_usd": str(self.loan_principal_usd),
            "costs": {
                "flash_loan_fee": str(self.costs.flash_loan_fee),
                "dex_fees": str(self.costs.dex_fees),
                "price_impact": str(self.costs.price_impact),
                "gas": str(self.costs.gas),
                "relay": str(self.costs.relay),
                "other": str(self.costs.other),
            },
            "max_gas_usd": str(self.max_gas_usd),
            "max_relay_usd": str(self.max_relay_usd),
            "minimum_net_profit_usd": str(self.minimum_net_profit_usd),
        }

    def _digest(self) -> str:
        encoded = json.dumps(self._canonical_payload(), sort_keys=True, separators=(",", ":")).encode()
        return keccak256_hex(encoded)


def build_economic_proof(
    *,
    route_hash: str,
    quote_hashes: Iterable[str],
    valuation_hash: str,
    final_settlement_usd: Decimal | int | str,
    loan_principal_usd: Decimal | int | str,
    costs: CostBreakdown,
    max_gas_usd: Decimal | int | str,
    max_relay_usd: Decimal | int | str,
    minimum_net_profit_usd: Decimal | int | str = STRICT_MIN_NET_PROFIT_USD,
    proof_hash: str = "",
) -> EconomicProof:
    """Build a deterministic proof and reject candidates at or below the floor."""
    proof = EconomicProof(
        schema_version=1,
        route_hash=route_hash,
        quote_hashes=tuple(quote_hashes),
        valuation_hash=valuation_hash,
        final_settlement_usd=final_settlement_usd,
        loan_principal_usd=loan_principal_usd,
        costs=costs,
        max_gas_usd=max_gas_usd,
        max_relay_usd=max_relay_usd,
        minimum_net_profit_usd=minimum_net_profit_usd,
        proof_hash=proof_hash,
    )
    if not proof.economically_valid:
        raise EconomicProofError("worst-case net profit does not exceed the strict minimum")
    return proof
