"""Generic deterministic exact two-or-more-leg cycle simulation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from .hashing import keccak256_hex
from .quote_snapshot import QuoteSnapshot

class CycleSimulationError(ValueError):
    """Raised when cycle quote evidence is inconsistent."""

@dataclass(frozen=True)
class CycleSimulation:
    chain_id:int
    block_number:int
    initial_amount:int
    final_amount:int
    legs:tuple[QuoteSnapshot,...]
    route_hash:str
    def __post_init__(self)->None:
        if len(self.legs)<2: raise CycleSimulationError("cycle requires at least two legs")
        if self.legs[0].amount_in!=self.initial_amount or self.legs[-1].amount_out!=self.final_amount:
            raise CycleSimulationError("cycle amount mismatch")
        for p,c in zip(self.legs,self.legs[1:]):
            if p.chain_id!=c.chain_id or p.block_number!=c.block_number:
                raise CycleSimulationError("cycle block/chain mismatch")
            if p.token_out.lower()!=c.token_in.lower() or p.amount_out!=c.amount_in:
                raise CycleSimulationError("cycle continuity broken")
        if self.legs[-1].token_out.lower()!=self.legs[0].token_in.lower():
            raise CycleSimulationError("cycle does not return to initial token")
        if self.route_hash!=compute_cycle_route_hash(self.legs):
            raise CycleSimulationError("route hash mismatch")

def compute_cycle_route_hash(legs:Sequence[QuoteSnapshot])->str:
    if len(legs)<2: raise CycleSimulationError("at least two legs required")
    try: payload=b"".join(bytes.fromhex(leg.quote_hash[2:]) for leg in legs)
    except (ValueError,AttributeError) as exc: raise CycleSimulationError("invalid quote hash") from exc
    return keccak256_hex(payload)

def simulate_cycle(legs:Sequence[QuoteSnapshot])->CycleSimulation:
    normalized=tuple(legs)
    if len(normalized)<2: raise CycleSimulationError("at least two legs required")
    return CycleSimulation(normalized[0].chain_id,normalized[0].block_number,normalized[0].amount_in,normalized[-1].amount_out,normalized,compute_cycle_route_hash(normalized))
