"""Convert exact transaction-level gas evidence into a conservative USD cost bound.

The native-token USD price is an external, evidence-backed input. This module
never fetches or invents a price and never treats gas as a percentage of loan size.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .gas_observation import GasObservation

class GasCostEvidenceError(ValueError):
    """Raised when gas USD evidence cannot be established safely."""

def _decimal(value: Decimal | int | str, field: str) -> Decimal:
    try:
        out = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise GasCostEvidenceError(f"{field} is not a valid decimal") from exc
    if not out.is_finite() or out <= 0:
        raise GasCostEvidenceError(f"{field} must be finite and positive")
    return out

@dataclass(frozen=True)
class GasCostEvidence:
    schema_version: int
    gas_observation: GasObservation
    native_usd_price: Decimal
    valuation_evidence_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise GasCostEvidenceError("unsupported gas cost schema")
        price = _decimal(self.native_usd_price, "native_usd_price")
        object.__setattr__(self, "native_usd_price", price)
        if not isinstance(self.valuation_evidence_hash, str) or len(self.valuation_evidence_hash) != 66 or not self.valuation_evidence_hash.startswith("0x"):
            raise GasCostEvidenceError("valuation_evidence_hash must be a 32-byte 0x hash")
        try:
            int(self.valuation_evidence_hash[2:], 16)
        except ValueError as exc:
            raise GasCostEvidenceError("valuation_evidence_hash must be hexadecimal") from exc

    @property
    def max_gas_cost_usd(self) -> Decimal:
        native = Decimal(self.gas_observation.max_gas_cost_native)
        return (native * self.native_usd_price) / Decimal(10**18)

def build_gas_cost_evidence(observation: GasObservation, *, native_usd_price: Decimal | int | str, valuation_evidence_hash: str) -> GasCostEvidence:
    """Build the conservative USD gas bound from non-secret evidence."""
    return GasCostEvidence(
        schema_version=1,
        gas_observation=observation,
        native_usd_price=native_usd_price,
        valuation_evidence_hash=valuation_evidence_hash.lower(),
    )
