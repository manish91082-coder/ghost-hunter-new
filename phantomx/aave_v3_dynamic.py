"""Live Aave V3 Polygon flash-loan liquidity and premium reader.

Read-only only. All market state is bound to one supplied MarketBlockSnapshot.
The pool/address-provider addresses are deployment configuration; the reserve
liquidity, flash premium and reserve flags are read live at the pinned block.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from .market_block import MarketBlockSnapshot, POLYGON_CHAIN_ID

AAVE_V3_POLYGON_POOL_ADDRESSES_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"
AAVE_V3_POLYGON_POOL = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"

GET_POOL_SELECTOR = "026b1d5f"
GET_RESERVE_DATA_SELECTOR = "35ea6a75"
FLASHLOAN_PREMIUM_TOTAL_SELECTOR = "074b2e43"
BALANCE_OF_SELECTOR = "70a08231"

ACTIVE_BIT = 56
PAUSED_BIT = 60
FLASHLOAN_ENABLED_BIT = 63
PERCENTAGE_FACTOR = 10_000
HALF_PERCENTAGE_FACTOR = 5_000


class AaveV3DynamicError(ValueError):
    """Raised when Aave dynamic state cannot be proven."""


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        ...


def _address_word(address: str) -> bytes:
    if not isinstance(address, str):
        raise AaveV3DynamicError("address must be a string")
    raw = address[2:] if address.startswith(("0x", "0X")) else address
    if len(raw) != 40:
        raise AaveV3DynamicError("address must contain exactly 20 bytes")
    try:
        data = bytes.fromhex(raw)
    except ValueError as exc:
        raise AaveV3DynamicError("address is not hexadecimal") from exc
    return b"\x00" * 12 + data


def _call_data(selector: str, *addresses: str) -> str:
    payload = bytes.fromhex(selector)
    for address in addresses:
        payload += _address_word(address)
    return "0x" + payload.hex()


def _decode_bytes(result: Any, label: str, min_bytes: int = 32) -> bytes:
    if isinstance(result, dict):
        raise AaveV3DynamicError(f"{label}: RPC error object")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise AaveV3DynamicError(f"{label}: malformed RPC result")
    try:
        raw = bytes.fromhex(result[2:])
    except ValueError as exc:
        raise AaveV3DynamicError(f"{label}: invalid hexadecimal result") from exc
    if len(raw) < min_bytes or len(raw) % 32:
        raise AaveV3DynamicError(f"{label}: malformed ABI result")
    return raw


def _decode_uint(result: Any, label: str) -> int:
    raw = _decode_bytes(result, label)
    return int.from_bytes(raw[:32], "big")


def _decode_address(result: Any, label: str) -> str:
    raw = _decode_bytes(result, label)
    address = raw[:32][-20:]
    if address == b"\x00" * 20:
        raise AaveV3DynamicError(f"{label}: zero address")
    return "0x" + address.hex()


def _percent_mul(value: int, percentage_bps: int) -> int:
    if value < 0 or percentage_bps < 0:
        raise AaveV3DynamicError("percentage multiplication inputs must be non-negative")
    if percentage_bps > PERCENTAGE_FACTOR:
        raise AaveV3DynamicError("percentage exceeds Aave PercentageMath range")
    product = value * percentage_bps
    return (product + HALF_PERCENTAGE_FACTOR) // PERCENTAGE_FACTOR


@dataclass(frozen=True)
class AaveFlashLiquiditySnapshot:
    chain_id: int
    block_number: int
    asset: str
    pool_addresses_provider: str
    pool: str
    a_token: str
    available_liquidity_raw: int
    flash_loan_premium_bps: int
    reserve_active: bool
    reserve_paused: bool
    flashloan_enabled: bool

    def __post_init__(self) -> None:
        if self.chain_id != POLYGON_CHAIN_ID:
            raise AaveV3DynamicError("Aave snapshot must be Polygon mainnet")
        if self.block_number < 0:
            raise AaveV3DynamicError("block number cannot be negative")
        if not isinstance(self.asset, str) or len(self.asset.replace("0x", "")) != 40:
            raise AaveV3DynamicError("asset must be a 20-byte address")
        if self.available_liquidity_raw <= 0:
            raise AaveV3DynamicError("available liquidity must be positive")
        if not 0 <= self.flash_loan_premium_bps <= PERCENTAGE_FACTOR:
            raise AaveV3DynamicError("invalid flash-loan premium")
        if not self.reserve_active:
            raise AaveV3DynamicError("Aave reserve is inactive")
        if self.reserve_paused:
            raise AaveV3DynamicError("Aave reserve is paused")
        if not self.flashloan_enabled:
            raise AaveV3DynamicError("Aave flashloan is disabled for this reserve")

    def premium_raw(self, amount_raw: int) -> int:
        if not isinstance(amount_raw, int) or isinstance(amount_raw, bool) or amount_raw <= 0:
            raise AaveV3DynamicError("flash-loan amount must be a positive integer")
        return _percent_mul(amount_raw, self.flash_loan_premium_bps)

    def repayment_raw(self, amount_raw: int) -> int:
        return amount_raw + self.premium_raw(amount_raw)

    def safe_borrow_ceiling_raw(self, *, safety_headroom_bps: int = 0) -> int:
        if not isinstance(safety_headroom_bps, int) or isinstance(safety_headroom_bps, bool):
            raise AaveV3DynamicError("safety_headroom_bps must be an integer")
        if not 0 <= safety_headroom_bps <= PERCENTAGE_FACTOR:
            raise AaveV3DynamicError("safety_headroom_bps out of range")
        ceiling = (
            self.available_liquidity_raw * (PERCENTAGE_FACTOR - safety_headroom_bps)
        ) // PERCENTAGE_FACTOR
        if ceiling <= 0:
            raise AaveV3DynamicError("no positive borrow ceiling after safety headroom")
        return ceiling


class AaveV3PolygonDynamicReader:
    """Read-only live Aave V3 Polygon reserve state."""

    def __init__(
        self,
        rpc: RpcTransport,
        *,
        pool_addresses_provider: str = AAVE_V3_POLYGON_POOL_ADDRESSES_PROVIDER,
    ) -> None:
        _address_word(pool_addresses_provider)
        self._rpc = rpc
        self.pool_addresses_provider = pool_addresses_provider

    def _pool_at(self, snapshot: MarketBlockSnapshot) -> str:
        result = self._rpc.call(
            "eth_call",
            [
                {"to": self.pool_addresses_provider, "data": "0x" + GET_POOL_SELECTOR},
                hex(snapshot.block_number),
            ],
        )
        return _decode_address(result, "Aave getPool")

    def snapshot(
        self,
        asset: str,
        block: MarketBlockSnapshot,
    ) -> AaveFlashLiquiditySnapshot:
        _address_word(asset)
        if block.chain_id != POLYGON_CHAIN_ID:
            raise AaveV3DynamicError("Aave reader requires Polygon mainnet")

        pool = self._pool_at(block)

        reserve_result = self._rpc.call(
            "eth_call",
            [
                {"to": pool, "data": _call_data(GET_RESERVE_DATA_SELECTOR, asset)},
                hex(block.block_number),
            ],
        )
        reserve_raw = _decode_bytes(reserve_result, "Aave getReserveData", min_bytes=32 * 9)
        config = int.from_bytes(reserve_raw[0:32], "big")
        a_token = "0x" + reserve_raw[8 * 32 + 12 : 9 * 32].hex()
        if a_token == "0x" + "00" * 20:
            raise AaveV3DynamicError("Aave reserve returned zero aToken")

        premium_result = self._rpc.call(
            "eth_call",
            [
                {"to": pool, "data": "0x" + FLASHLOAN_PREMIUM_TOTAL_SELECTOR},
                hex(block.block_number),
            ],
        )
        premium_bps = _decode_uint(premium_result, "Aave flashloan premium")

        balance_result = self._rpc.call(
            "eth_call",
            [
                {"to": asset, "data": _call_data(BALANCE_OF_SELECTOR, a_token)},
                hex(block.block_number),
            ],
        )
        available = _decode_uint(balance_result, "Aave underlying liquidity")

        return AaveFlashLiquiditySnapshot(
            chain_id=block.chain_id,
            block_number=block.block_number,
            asset=asset,
            pool_addresses_provider=self.pool_addresses_provider,
            pool=pool,
            a_token=a_token,
            available_liquidity_raw=available,
            flash_loan_premium_bps=premium_bps,
            reserve_active=bool(config & (1 << ACTIVE_BIT)),
            reserve_paused=bool(config & (1 << PAUSED_BIT)),
            flashloan_enabled=bool(config & (1 << FLASHLOAN_ENABLED_BIT)),
        )
