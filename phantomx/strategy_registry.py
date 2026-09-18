"""Controlled strategy registry for PhantomX.

A strategy record describes a search/execution family. Registration does not
authorize production execution. Every non-canonical strategy starts in
DISCOVERY_ONLY and must satisfy its adapter, quote, economics, adversarial,
fork, and authority gates before promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class StrategyStatus(str, Enum):
    CANONICAL = "CANONICAL"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    DISABLED = "DISABLED"


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    name: str
    status: StrategyStatus
    chain_id: int
    flash_liquidity: tuple[str, ...]
    venues: tuple[str, ...]
    route_family: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.strategy_id or not self.name:
            raise ValueError("strategy identity is required")
        if self.chain_id != 137:
            raise ValueError("current strategy registry is Polygon-only")
        if not self.flash_liquidity or not self.venues:
            raise ValueError("strategy must declare liquidity and venues")
        if not self.route_family:
            raise ValueError("route family is required")


class StrategyRegistry:
    def __init__(self, specs: Iterable[StrategySpec] = ()) -> None:
        self._specs: dict[str, StrategySpec] = {}
        for spec in specs:
            self.add(spec)

    def add(self, spec: StrategySpec) -> None:
        if spec.strategy_id in self._specs:
            raise ValueError("duplicate strategy_id")
        self._specs[spec.strategy_id] = spec

    def get(self, strategy_id: str) -> StrategySpec:
        return self._specs[strategy_id]

    def enabled(self) -> tuple[StrategySpec, ...]:
        return tuple(s for s in self._specs.values() if s.status != StrategyStatus.DISABLED)

    def production(self) -> tuple[StrategySpec, ...]:
        return tuple(s for s in self._specs.values() if s.status == StrategyStatus.CANONICAL)

    def discovery_only(self) -> tuple[StrategySpec, ...]:
        return tuple(s for s in self._specs.values() if s.status == StrategyStatus.DISCOVERY_ONLY)


DEFAULT_STRATEGIES = StrategyRegistry(
    (
        StrategySpec(
            "S0-DIRECT-QS-V3",
            "QuickSwap V2 ↔ Uniswap V3 direct A→B→A",
            StrategyStatus.CANONICAL,
            137,
            ("Aave V3",),
            ("QuickSwap V2", "Uniswap V3"),
            "direct_two_leg_cross_venue",
            "Current certified execution scope.",
        ),
        StrategySpec(
            "S1-QS-V3",
            "QuickSwap V3 ↔ Uniswap V3",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Aave V3",),
            ("QuickSwap V3", "Uniswap V3"),
            "direct_two_leg_cross_venue",
            "Uses Algebra poolByPair discovery and quote-returned dynamic fee; no fixed fee-tier grid is assumed.",
        ),
        StrategySpec(
            "S2-UV4-V3",
            "Uniswap V4 ↔ Uniswap V3",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Aave V3",),
            ("Uniswap V4", "Uniswap V3"),
            "direct_two_leg_cross_venue",
            "Polygon V4 deployment is present; adapter/proof is not yet certified.",
        ),
        StrategySpec(
            "S3-RAMSES-UV3",
            "Ramses V3 ↔ Uniswap V3",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Aave V3",),
            ("Ramses V3", "Uniswap V3"),
            "direct_two_leg_cross_venue",
            "Requires Ramses exact-quote adapter and pool discovery.",
        ),
        StrategySpec(
            "S4-BALANCER-UV3",
            "Balancer V2 ↔ Uniswap V3",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Aave V3",),
            ("Balancer V2", "Uniswap V3"),
            "direct_two_leg_cross_venue",
            "Requires Balancer Vault queryBatchSwap exact adapter/proof.",
        ),
        StrategySpec(
            "S5-CURVE-UV3",
            "Curve ↔ Uniswap V3",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Aave V3",),
            ("Curve", "Uniswap V3"),
            "direct_two_leg_cross_venue",
            "Requires Curve pool discovery/exact quote adapter.",
        ),
        StrategySpec(
            "S6-TRIANGULAR",
            "Triangular multi-hop",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Aave V3",),
            ("Multiple Polygon venues",),
            "three_or_more_legs",
            "Requires a separate route simulator and economic proof for multi-hop topology.",
        ),
        StrategySpec(
            "S7-STABLE-STABLE",
            "Stablecoin cross-venue",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Aave V3",),
            ("Multiple Polygon venues",),
            "stablecoin_cross_venue",
            "Requires canonical token mapping and dynamic depeg/fee/liquidity controls.",
        ),
        StrategySpec(
            "S8-ALTERNATIVE-FLASH-LIQUIDITY",
            "Alternative flash-liquidity source",
            StrategyStatus.DISCOVERY_ONLY,
            137,
            ("Multiple flash liquidity providers",),
            ("Multiple Polygon venues",),
            "flash_source_variant",
            "Requires provider-specific callback/repayment proof before activation.",
        ),
    )
)
