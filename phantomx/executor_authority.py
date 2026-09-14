"""Fail-closed executor authority attestation for Phase 19.

This layer does not sign or submit transactions. It binds a deployed executor
address, its observed owner, Polygon chain identity, observation block, and
runtime code hash into immutable evidence. The execution coordinator can use
this evidence to prove that the cryptographic signer address is also the actual
owner/controller of the deployed executor instance.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .hashing import keccak256_hex


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


@dataclass(frozen=True)
class ExecutorAuthorityEvidence:
    """Immutable observation that a sender owns a concrete deployed executor."""

    schema_version: int
    chain_id: int
    executor: str
    owner: str
    observed_block: int
    runtime_code_hash: str
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ExecutorAuthorityError("unsupported executor authority schema")
        if self.chain_id != 137:
            raise ExecutorAuthorityError("Phase-19 executor authority is Polygon-only")
        if not isinstance(self.observed_block, int) or isinstance(self.observed_block, bool) or self.observed_block < 0:
            raise ExecutorAuthorityError("observed block must be a non-negative integer")
        object.__setattr__(self, "executor", _address(self.executor, "executor"))
        object.__setattr__(self, "owner", _address(self.owner, "owner"))
        object.__setattr__(self, "runtime_code_hash", _hash(self.runtime_code_hash, "runtime_code_hash"))
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
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return keccak256_hex(encoded)


def verify_executor_authority(
    evidence: ExecutorAuthorityEvidence,
    *,
    chain_id: int,
    executor: str,
    sender: str,
    minimum_observed_block: int = 0,
) -> None:
    """Require deployed executor ownership to exactly match the execution sender."""
    if chain_id != 137:
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
