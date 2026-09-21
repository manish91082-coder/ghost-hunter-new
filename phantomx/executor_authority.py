"""Fail-closed executor authority attestation for Phase 19.

This layer does not sign or submit transactions. It binds a deployed executor
address, its observed owner, Polygon chain identity, observation block, runtime
code hash, and provider provenance into immutable evidence. The execution
coordinator can use this evidence to prove that the cryptographic signer
address is also the actual owner/controller of the deployed executor instance.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .hashing import keccak256_hex
from .polygon_nonce import parse_quantity
from .polygon_rpc import POLYGON_CHAIN_ID, RPCProvider


class ExecutorAuthorityError(ValueError):
    """Raised when executor ownership evidence is malformed or inconsistent."""


def _address(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ExecutorAuthorityError(f"{field} must be a 20-byte 0x address")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ExecutorAuthorityError(f"{field} is not valid hexadecimal") from exc
    if raw == b"\x00" * 20:
        raise ExecutorAuthorityError(f"{field} must be non-zero")
    return value.lower()


def _hash(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise ExecutorAuthorityError(f"{field} must be a 32-byte 0x hash")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise ExecutorAuthorityError(f"{field} is not hexadecimal") from exc
    return value.lower()


def _rpc_result(response: Mapping[str, Any], method: str) -> Any:
    if not isinstance(response, Mapping):
        raise ExecutorAuthorityError(f"{method}: response must be an object")
    if response.get("error") is not None:
        raise ExecutorAuthorityError(f"{method}: RPC error")
    if "result" not in response:
        raise ExecutorAuthorityError(f"{method}: missing result")
    return response["result"]


@dataclass(frozen=True)
class ExecutorAuthorityEvidence:
    """Immutable observation that a sender owns a concrete deployed executor."""

    schema_version: int
    chain_id: int
    executor: str
    owner: str
    observed_block: int
    runtime_code_hash: str
    attesting_provider_names: tuple[str, ...] = ()
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ExecutorAuthorityError("unsupported executor authority schema")
        if self.chain_id != POLYGON_CHAIN_ID:
            raise ExecutorAuthorityError("Phase-19 executor authority is Polygon-only")
        if not isinstance(self.observed_block, int) or isinstance(self.observed_block, bool) or self.observed_block < 0:
            raise ExecutorAuthorityError("observed block must be a non-negative integer")
        object.__setattr__(self, "executor", _address(self.executor, "executor"))
        object.__setattr__(self, "owner", _address(self.owner, "owner"))
        object.__setattr__(self, "runtime_code_hash", _hash(self.runtime_code_hash, "runtime_code_hash"))
        if not isinstance(self.attesting_provider_names, tuple) or not all(
            isinstance(name, str) and name.strip() for name in self.attesting_provider_names
        ):
            raise ExecutorAuthorityError("attesting provider names must be a tuple of non-empty strings")
        if len(set(self.attesting_provider_names)) != len(self.attesting_provider_names):
            raise ExecutorAuthorityError("attesting provider names must be unique")
        object.__setattr__(self, "attesting_provider_names", tuple(self.attesting_provider_names))
        expected = self._digest()
        if self.evidence_hash:
            if self.evidence_hash.lower() != expected:
                raise ExecutorAuthorityError("executor authority evidence hash mismatch")
            object.__setattr__(self, "evidence_hash", self.evidence_hash.lower())
        else:
            object.__setattr__(self, "evidence_hash", expected)

    def _digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "chain_id": self.chain_id,
            "executor": self.executor,
            "owner": self.owner,
            "observed_block": self.observed_block,
            "runtime_code_hash": self.runtime_code_hash,
            "attesting_provider_names": list(self.attesting_provider_names),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return keccak256_hex(encoded)


def runtime_code_binding_hash(evidence: ExecutorAuthorityEvidence) -> str:
    """Return a stable identity for one deployed owner/code instance across blocks."""
    if not isinstance(evidence, ExecutorAuthorityEvidence):
        raise ExecutorAuthorityError("runtime code binding requires executor authority evidence")
    payload = {
        "schema_version": evidence.schema_version,
        "chain_id": evidence.chain_id,
        "executor": evidence.executor,
        "owner": evidence.owner,
        "runtime_code_hash": evidence.runtime_code_hash,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return keccak256_hex(encoded)


def verify_executor_authority_freshness(
    evidence: ExecutorAuthorityEvidence,
    *,
    current_observed_block: int,
    maximum_age_blocks: int,
) -> None:
    """Reject replay of authority evidence outside an explicit block-age window."""
    if not isinstance(evidence, ExecutorAuthorityEvidence):
        raise ExecutorAuthorityError("authority freshness requires executor authority evidence")
    if not isinstance(current_observed_block, int) or isinstance(current_observed_block, bool) or current_observed_block < 0:
        raise ExecutorAuthorityError("current observed block must be a non-negative integer")
    if not isinstance(maximum_age_blocks, int) or isinstance(maximum_age_blocks, bool) or maximum_age_blocks <= 0:
        raise ExecutorAuthorityError("maximum observation age must be a positive integer")
    if evidence.observed_block > current_observed_block:
        raise ExecutorAuthorityError("authority evidence is from the future relative to current observation")
    age = current_observed_block - evidence.observed_block
    if age > maximum_age_blocks:
        raise ExecutorAuthorityError("stale executor authority evidence exceeds observation-age policy")


def observe_executor_authority(provider: RPCProvider, executor: str) -> ExecutorAuthorityEvidence:
    """Observe owner and runtime code at one explicit Polygon block."""
    executor = _address(executor, "executor")
    chain_raw = _rpc_result(provider.transport("eth_chainId"), "eth_chainId")
    try:
        chain_id = parse_quantity(chain_raw, field="chain id")
    except Exception as exc:
        raise ExecutorAuthorityError(str(exc)) from exc
    if chain_id != POLYGON_CHAIN_ID:
        raise ExecutorAuthorityError(f"unexpected chain id: {chain_id}")

    try:
        block_number = parse_quantity(
            _rpc_result(provider.transport("eth_blockNumber"), "eth_blockNumber"),
            field="block number",
        )
    except Exception as exc:
        raise ExecutorAuthorityError(str(exc)) from exc
    block_tag = "0x" + format(block_number, "x")

    owner_result = _rpc_result(
        provider.transport("eth_call", {"to": executor, "data": "0x8da5cb5b"}, block_tag),
        "eth_call owner",
    )
    if not isinstance(owner_result, str) or not owner_result.startswith("0x"):
        raise ExecutorAuthorityError("owner() result must be hex")
    try:
        owner_encoded = bytes.fromhex(owner_result[2:])
    except ValueError as exc:
        raise ExecutorAuthorityError("owner() result is not valid hexadecimal") from exc
    if len(owner_encoded) != 32 or owner_encoded[:12] != b"\x00" * 12:
        raise ExecutorAuthorityError("owner() result is not a canonical ABI address word")
    owner = "0x" + owner_encoded[12:].hex()

    code_result = _rpc_result(
        provider.transport("eth_getCode", executor, block_tag),
        "eth_getCode",
    )
    if not isinstance(code_result, str) or not code_result.startswith("0x") or len(code_result) <= 2 or (len(code_result) - 2) % 2:
        raise ExecutorAuthorityError("runtime code must be non-empty even-length hex")
    try:
        runtime_code = bytes.fromhex(code_result[2:])
    except ValueError as exc:
        raise ExecutorAuthorityError("runtime code is not valid hexadecimal") from exc

    return ExecutorAuthorityEvidence(
        schema_version=1,
        chain_id=chain_id,
        executor=executor,
        owner=owner,
        observed_block=block_number,
        runtime_code_hash=keccak256_hex(runtime_code),
        attesting_provider_names=(provider.name,),
    )


def _observe_authority_at_block(provider: RPCProvider, executor: str, block_number: int) -> tuple[str, str]:
    """Read owner and runtime bytecode at a caller-selected common block."""
    block_tag = "0x" + format(block_number, "x")
    owner_result = _rpc_result(
        provider.transport("eth_call", {"to": executor, "data": "0x8da5cb5b"}, block_tag),
        f"{provider.name}: eth_call owner",
    )
    if not isinstance(owner_result, str) or not owner_result.startswith("0x"):
        raise ExecutorAuthorityError(f"{provider.name}: owner() result must be hex")
    try:
        owner_encoded = bytes.fromhex(owner_result[2:])
    except ValueError as exc:
        raise ExecutorAuthorityError(f"{provider.name}: owner() result is not valid hexadecimal") from exc
    if len(owner_encoded) != 32 or owner_encoded[:12] != b"\x00" * 12:
        raise ExecutorAuthorityError(f"{provider.name}: owner() result is not a canonical ABI address word")
    owner = _address("0x" + owner_encoded[12:].hex(), f"{provider.name}: owner")

    code_result = _rpc_result(
        provider.transport("eth_getCode", executor, block_tag),
        f"{provider.name}: eth_getCode",
    )
    if not isinstance(code_result, str) or not code_result.startswith("0x") or len(code_result) <= 2 or (len(code_result) - 2) % 2:
        raise ExecutorAuthorityError(f"{provider.name}: runtime code must be non-empty even-length hex")
    try:
        runtime_code = bytes.fromhex(code_result[2:])
    except ValueError as exc:
        raise ExecutorAuthorityError(f"{provider.name}: runtime code is not valid hexadecimal") from exc
    return owner, keccak256_hex(runtime_code)


def observe_executor_authority_quorum(
    providers: Sequence[RPCProvider],
    executor: str,
    *,
    quorum: int,
) -> ExecutorAuthorityEvidence:
    """Require provider quorum on one common Polygon block for owner and code."""
    executor = _address(executor, "executor")
    if not providers:
        raise ExecutorAuthorityError("at least one provider is required")
    if not isinstance(quorum, int) or isinstance(quorum, bool) or quorum <= 0 or quorum > len(providers):
        raise ExecutorAuthorityError("quorum must be between one and provider count")
    names = [provider.name for provider in providers]
    if len(set(names)) != len(names):
        raise ExecutorAuthorityError("provider names must be unique")

    blocks: list[int] = []
    for provider in providers:
        chain_raw = _rpc_result(provider.transport("eth_chainId"), f"{provider.name}: eth_chainId")
        try:
            chain_id = parse_quantity(chain_raw, field=f"{provider.name} chain id")
        except Exception as exc:
            raise ExecutorAuthorityError(str(exc)) from exc
        if chain_id != POLYGON_CHAIN_ID:
            raise ExecutorAuthorityError(f"{provider.name}: unexpected chain id: {chain_id}")
        try:
            block_number = parse_quantity(
                _rpc_result(provider.transport("eth_blockNumber"), f"{provider.name}: eth_blockNumber"),
                field=f"{provider.name} block number",
            )
        except Exception as exc:
            raise ExecutorAuthorityError(str(exc)) from exc
        blocks.append(block_number)

    common_block = min(blocks)
    observations: dict[tuple[str, str], list[str]] = {}
    for provider in providers:
        owner, runtime_hash = _observe_authority_at_block(provider, executor, common_block)
        observations.setdefault((owner, runtime_hash), []).append(provider.name)

    ranked = sorted(observations.items(), key=lambda item: (-len(item[1]), item[0]))
    winner_key, winner_providers = ranked[0]
    if len(winner_providers) < quorum:
        raise ExecutorAuthorityError("executor authority provider quorum not reached")
    if len(ranked) > 1 and len(ranked[1][1]) == len(winner_providers):
        raise ExecutorAuthorityError("executor authority provider quorum is ambiguous")

    owner, runtime_hash = winner_key
    return ExecutorAuthorityEvidence(
        schema_version=1,
        chain_id=POLYGON_CHAIN_ID,
        executor=executor,
        owner=owner,
        observed_block=common_block,
        runtime_code_hash=runtime_hash,
        attesting_provider_names=tuple(sorted(winner_providers)),
    )


def verify_executor_authority(
    evidence: ExecutorAuthorityEvidence,
    *,
    chain_id: int,
    executor: str,
    sender: str,
    minimum_observed_block: int = 0,
) -> None:
    """Require deployed executor ownership to exactly match the execution sender."""
    if chain_id != POLYGON_CHAIN_ID:
        raise ExecutorAuthorityError("execution chain is not Polygon")
    if evidence.chain_id != chain_id:
        raise ExecutorAuthorityError("authority evidence chain does not match execution chain")
    if evidence.executor != _address(executor, "executor"):
        raise ExecutorAuthorityError("authority evidence executor does not match execution target")
    if evidence.owner != _address(sender, "sender"):
        raise ExecutorAuthorityError("deployed executor owner does not match authorized sender")
    if not isinstance(minimum_observed_block, int) or isinstance(minimum_observed_block, bool) or minimum_observed_block < 0:
        raise ExecutorAuthorityError("minimum observed block must be a non-negative integer")
    if evidence.observed_block < minimum_observed_block:
        raise ExecutorAuthorityError("executor authority evidence predates the proven execution block")
    if evidence.runtime_code_hash == "0x" + "00" * 32:
        raise ExecutorAuthorityError("executor runtime code hash is empty")
