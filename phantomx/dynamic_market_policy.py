"""Deterministic primitives for dynamic market constraints."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

V3_FEE_SCALE = 1_000_000
WEI_PER_NATIVE = 10**18

@dataclass(frozen=True)
class DynamicLoanInputs:
    aave_available_raw: int
    route_input_ceiling_raw: int
    price_impact_ceiling_raw: int
    system_hard_cap_raw: int | None = None
    safety_headroom_bps: int = 0

    def __post_init__(self):
        for name, value in (("aave_available_raw", self.aave_available_raw),
                            ("route_input_ceiling_raw", self.route_input_ceiling_raw),
                            ("price_impact_ceiling_raw", self.price_impact_ceiling_raw)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.system_hard_cap_raw is not None and (
            not isinstance(self.system_hard_cap_raw, int) or isinstance(self.system_hard_cap_raw, bool) or self.system_hard_cap_raw < 0):
            raise ValueError("system_hard_cap_raw must be a non-negative integer or None")
        if not isinstance(self.safety_headroom_bps, int) or isinstance(self.safety_headroom_bps, bool) or not 0 <= self.safety_headroom_bps <= 10_000:
            raise ValueError("safety_headroom_bps must be between 0 and 10000")

def compute_dynamic_loan_ceiling(inputs: DynamicLoanInputs) -> int:
    if inputs.aave_available_raw <= 0:
        raise ValueError("Aave live liquidity is zero/unavailable")
    aave_safe = (inputs.aave_available_raw * (10_000 - inputs.safety_headroom_bps)) // 10_000
    values = [aave_safe, inputs.route_input_ceiling_raw, inputs.price_impact_ceiling_raw]
    if inputs.system_hard_cap_raw is not None:
        values.append(inputs.system_hard_cap_raw)
    ceiling = min(values)
    if ceiling <= 0:
        raise ValueError("no positive loan ceiling can be proven")
    return ceiling

def compute_uniswap_v3_swap_fee_raw(amount_in_raw: int, fee_tier: int) -> int:
    if not isinstance(amount_in_raw, int) or isinstance(amount_in_raw, bool) or amount_in_raw < 0:
        raise ValueError("amount_in_raw must be a non-negative integer")
    if not isinstance(fee_tier, int) or isinstance(fee_tier, bool) or not 0 <= fee_tier <= V3_FEE_SCALE:
        raise ValueError("fee_tier must be between 0 and 1_000_000")
    return (amount_in_raw * fee_tier) // V3_FEE_SCALE

def compute_gas_cost_usd(*, gas_used: int, effective_gas_price_wei: int, native_usd_price: Decimal) -> Decimal:
    if not isinstance(gas_used, int) or isinstance(gas_used, bool) or gas_used < 0:
        raise ValueError("gas_used must be a non-negative integer")
    if not isinstance(effective_gas_price_wei, int) or isinstance(effective_gas_price_wei, bool) or effective_gas_price_wei < 0:
        raise ValueError("effective_gas_price_wei must be a non-negative integer")
    if not isinstance(native_usd_price, Decimal) or not native_usd_price.is_finite() or native_usd_price < 0:
        raise ValueError("native_usd_price must be a finite non-negative Decimal")
    return (Decimal(gas_used * effective_gas_price_wei) / Decimal(WEI_PER_NATIVE)) * native_usd_price