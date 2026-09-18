"""Read-only exact execution-path gas observation for Polygon.

This module estimates the gas units of an exact transaction envelope at a
pinned block and observes EIP-1559 fee inputs. It never signs or submits.
Gas is deliberately independent of loan principal.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .execution import TransactionEnvelope

class GasObservationError(ValueError):
    """Raised when exact gas evidence cannot be established safely."""

def _hex_uint(value: object, field: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise GasObservationError(f"{field} must be 0x-prefixed hex")
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise GasObservationError(f"{field} must be hexadecimal") from exc
    if parsed < 0:
        raise GasObservationError(f"{field} cannot be negative")
    return parsed

def _address(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 42:
        raise GasObservationError(f"{field} must be a 20-byte address")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise GasObservationError(f"{field} is not valid hex") from exc
    if len(raw) != 20 or raw == bytes(20):
        raise GasObservationError(f"{field} must be non-zero")
    return value

@dataclass(frozen=True)
class GasObservation:
    schema_version: int
    chain_id: int
    block_number: int
    gas_estimate: int
    gas_limit: int
    base_fee_per_gas: int
    priority_fee_per_gas: int
    max_fee_per_gas: int

    def __post_init__(self) -> None:
        for name in ("chain_id", "block_number", "gas_estimate", "gas_limit", "base_fee_per_gas", "priority_fee_per_gas", "max_fee_per_gas"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise GasObservationError(f"{name} must be a non-negative integer")
        if self.schema_version != 1:
            raise GasObservationError("unsupported gas observation schema")
        if self.chain_id != 137:
            raise GasObservationError("gas observation must be Polygon-mainnet scoped")
        if self.gas_estimate <= 0 or self.gas_limit < self.gas_estimate:
            raise GasObservationError("gas limit must cover positive gas estimate")
        if self.max_fee_per_gas < self.priority_fee_per_gas:
            raise GasObservationError("max fee must cover priority fee")

    @property
    def gas_headroom_units(self) -> int:
        return self.gas_limit - self.gas_estimate

    @property
    def max_gas_cost_native(self) -> int:
        return self.gas_limit * self.max_fee_per_gas

def _gas_transaction(envelope: TransactionEnvelope) -> dict[str, Any]:
    return {
        "from": _address(envelope.sender, "sender"),
        "to": _address(envelope.executor, "executor"),
        "data": "0x" + envelope.calldata.hex(),
        "nonce": hex(envelope.nonce),
        "value": "0x0",
    }

def observe_exact_gas(rpc, envelope: TransactionEnvelope, *, block_number: int, gas_safety_bps: int = 2000) -> GasObservation:
    """Estimate exact gas at a pinned block and derive a bounded EIP-1559 envelope."""
    if not isinstance(block_number, int) or isinstance(block_number, bool) or block_number < 0:
        raise GasObservationError("block_number must be a non-negative integer")
    if not isinstance(gas_safety_bps, int) or isinstance(gas_safety_bps, bool) or not 0 <= gas_safety_bps <= 10_000:
        raise GasObservationError("gas_safety_bps must be between 0 and 10000")

    chain_raw = rpc.call("eth_chainId", ())
    chain_id = _hex_uint(chain_raw.get("result"), "chain_id")
    if chain_id != 137:
        raise GasObservationError("RPC is not Polygon mainnet")

    block_raw = rpc.call("eth_getBlockByNumber", (hex(block_number), False))
    block = block_raw.get("result")
    if not isinstance(block, Mapping):
        raise GasObservationError("pinned block observation is unavailable")
    observed_number = _hex_uint(block.get("number"), "block.number")
    if observed_number != block_number:
        raise GasObservationError("RPC returned a different block than requested")
    base_fee = _hex_uint(block.get("baseFeePerGas"), "block.baseFeePerGas")

    estimate_raw = rpc.call("eth_estimateGas", (_gas_transaction(envelope), hex(block_number)))
    gas_estimate = _hex_uint(estimate_raw.get("result"), "gas_estimate")
    if gas_estimate <= 0:
        raise GasObservationError("RPC returned a non-positive gas estimate")

    try:
        priority_raw = rpc.call("eth_maxPriorityFeePerGas", ())
        priority_fee = _hex_uint(priority_raw.get("result"), "priority_fee")
    except Exception:
        price_raw = rpc.call("eth_gasPrice", ())
        observed_price = _hex_uint(price_raw.get("result"), "gas_price")
        priority_fee = observed_price if observed_price < base_fee else observed_price - base_fee

    gas_limit = gas_estimate + (gas_estimate * gas_safety_bps + 9999) // 10_000
    max_fee = base_fee * 2 + priority_fee
    return GasObservation(
        schema_version=1, chain_id=chain_id, block_number=block_number,
        gas_estimate=gas_estimate, gas_limit=gas_limit,
        base_fee_per_gas=base_fee, priority_fee_per_gas=priority_fee,
        max_fee_per_gas=max_fee,
    )
