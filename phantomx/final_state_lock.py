"""Final requote and state-lock boundary for PhantomX.

A discovery-time EconomicProof is never reused as final execution evidence.
The final state lock must bind a freshly requoted RouteSimulation and a
freshly rebuilt EconomicProof to the exact current block, valuation evidence,
and loan amount. This module is pure and performs no RPC, signing, or submit.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .economic_proof import EconomicProof
from .hashing import keccak256_hex
from .opportunity_discovery import OpportunityCandidate


class FinalStateLockError(ValueError):
    """Raised when final execution state cannot be safely locked."""


@dataclass(frozen=True)
class FinalStateLock:
    schema_version: int
    chain_id: int
    block_number: int
    token_a: str
    token_b: str
    venue_path: str
    loan_amount: int
    route_hash: str
    quote_hashes: tuple[str, ...]
    valuation_hash: str
    economic_proof_hash: str
    minimum_net_profit_usd: str
    state_lock_hash: str = ""

    def _payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "chain_id": self.chain_id,
            "block_number": self.block_number,
            "token_a": self.token_a.lower(),
            "token_b": self.token_b.lower(),
            "venue_path": self.venue_path,
            "loan_amount": self.loan_amount,
            "route_hash": self.route_hash.lower(),
            "quote_hashes": list(self.quote_hashes),
            "valuation_hash": self.valuation_hash.lower(),
            "economic_proof_hash": self.economic_proof_hash.lower(),
            "minimum_net_profit_usd": self.minimum_net_profit_usd,
        }

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise FinalStateLockError("unsupported final state-lock schema")
        if self.chain_id != 137:
            raise FinalStateLockError("final state lock must be Polygon mainnet")
        if self.block_number < 0 or self.loan_amount <= 0:
            raise FinalStateLockError("invalid final block or loan amount")
        if not self.token_a or not self.token_b or self.token_a.lower() == self.token_b.lower():
            raise FinalStateLockError("invalid token pair")
        for name, value in (
            ("route_hash", self.route_hash),
            ("valuation_hash", self.valuation_hash),
            ("economic_proof_hash", self.economic_proof_hash),
        ):
            if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
                raise FinalStateLockError(f"{name} must be a 32-byte hash")
        if not self.quote_hashes:
            raise FinalStateLockError("final state lock needs quote hashes")
        expected = keccak256_hex(json.dumps(self._payload(), sort_keys=True, separators=(",", ":")).encode())
        if self.state_lock_hash:
            if self.state_lock_hash.lower() != expected:
                raise FinalStateLockError("state lock hash mismatch")
            object.__setattr__(self, "state_lock_hash", self.state_lock_hash.lower())
        else:
            object.__setattr__(self, "state_lock_hash", expected)


def lock_final_requote(
    *,
    candidate: OpportunityCandidate,
    final_proof: EconomicProof,
    current_block_number: int,
    final_valuation_hash: str,
    final_gas_block_number: int,
) -> FinalStateLock:
    """Accept only a fresh, economically valid proof at the exact current block."""
    simulation = candidate.simulation

    if not isinstance(current_block_number, int) or isinstance(current_block_number, bool) or current_block_number < 0:
        raise FinalStateLockError("current_block_number must be a non-negative integer")
    if simulation.block_number != current_block_number:
        raise FinalStateLockError("final requote is stale: block mismatch")
    if final_gas_block_number != current_block_number:
        raise FinalStateLockError("final gas evidence is stale: block mismatch")
    if not isinstance(final_valuation_hash, str) or final_valuation_hash.lower() != final_proof.valuation_hash.lower():
        raise FinalStateLockError("final valuation hash does not match EconomicProof")
    if not final_proof.economically_valid:
        raise FinalStateLockError("final EconomicProof is below the strict net-profit floor")
    if final_proof.route_hash.lower() != simulation.route_hash.lower():
        raise FinalStateLockError("final proof route does not match final requote")
    expected_quotes = tuple(leg.quote_hash.lower() for leg in simulation.legs)
    if tuple(item.lower() for item in final_proof.quote_hashes) != expected_quotes:
        raise FinalStateLockError("final proof quote hashes do not match final requote")
    expected_loan_usd = final_proof.loan_principal_usd
    actual_loan_usd = simulation.initial_amount / 10**6
    if expected_loan_usd != expected_loan_usd.__class__(str(actual_loan_usd)):
        raise FinalStateLockError("final proof loan principal does not match requote")

    return FinalStateLock(
        schema_version=1,
        chain_id=simulation.chain_id,
        block_number=current_block_number,
        token_a=candidate.token_a,
        token_b=candidate.token_b,
        venue_path=candidate.venue_path,
        loan_amount=candidate.loan_amount,
        route_hash=simulation.route_hash,
        quote_hashes=expected_quotes,
        valuation_hash=final_proof.valuation_hash,
        economic_proof_hash=final_proof.proof_hash,
        minimum_net_profit_usd=str(final_proof.minimum_net_profit_usd),
    )
