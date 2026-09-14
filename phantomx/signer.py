"""Fail-closed Phase-19 signer boundary with cryptographic sender recovery.

The signer accepts only a Governor-approved transaction whose exact intent,
authorization, and envelope identities still match. The concrete EIP-1559
signer serializes the exact Ethereum transaction, and the boundary recovers the
sender from the signed bytes so the cryptographic signing identity must equal
ExecutionIntent.sender. No RPC, relay, or broadcaster is used here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import rlp
from eth_keys import keys
from eth_keys.exceptions import BadSignature

from .execution import Authorization, ExecutionIntent, TransactionEnvelope
from .governor import GovernorDecision
from .hashing import keccak256_hex


class SignerError(ValueError):
    """Raised when a transaction is unsafe or impossible to sign."""


class TransactionSigner(Protocol):
    def sign(self, envelope: TransactionEnvelope) -> bytes:
        """Return the serialized signed transaction bytes."""


def _rlp_uint(value: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise SignerError("transaction integer fields must be non-negative integers")
    return b"" if value == 0 else value.to_bytes((value.bit_length() + 7) // 8, "big")


def _hex_address(value: str, field: str) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 42:
        raise SignerError(f"{field} must be a 20-byte 0x address")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise SignerError(f"{field} is not valid hexadecimal") from exc
    if len(raw) != 20 or raw == b"\x00" * 20:
        raise SignerError(f"{field} must be a non-zero 20-byte address")
    return raw


@dataclass(frozen=True)
class SignedTransaction:
    """Immutable signed artifact bound to the exact governed envelope."""

    intent_hash: str
    governor_decision_hash: str
    transaction_hash: str
    raw_transaction: bytes

    def __post_init__(self) -> None:
        for name in ("intent_hash", "governor_decision_hash", "transaction_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
                raise SignerError(f"{name} must be a 32-byte 0x hash")
        if not isinstance(self.raw_transaction, bytes) or not self.raw_transaction:
            raise SignerError("signed transaction bytes are required")
        expected = keccak256_hex(self.raw_transaction)
        if self.transaction_hash.lower() != expected:
            raise SignerError("signed transaction hash does not match raw transaction")


@dataclass(frozen=True)
class EthereumEip1559Signer:
    """Minimal network-free EIP-1559 signer with explicit Ethereum identity."""

    private_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.private_key, str) or not self.private_key.startswith("0x") or len(self.private_key) != 66:
            raise SignerError("private_key must be a 32-byte 0x hex key")
        try:
            key = keys.PrivateKey(bytes.fromhex(self.private_key[2:]))
        except Exception as exc:
            raise SignerError("private_key is invalid") from exc
        object.__setattr__(self, "private_key", "0x" + key.to_bytes().hex())

    @property
    def address(self) -> str:
        return keys.PrivateKey(bytes.fromhex(self.private_key[2:])).public_key.to_checksum_address().lower()

    def sign(self, envelope: TransactionEnvelope) -> bytes:
        if envelope.chain_id <= 0:
            raise SignerError("transaction chain id must be positive")
        if envelope.nonce < 0:
            raise SignerError("transaction nonce cannot be negative")
        if envelope.gas_limit <= 0:
            raise SignerError("transaction gas limit must be positive")
        if envelope.max_fee_per_gas < envelope.max_priority_fee_per_gas or envelope.max_priority_fee_per_gas < 0:
            raise SignerError("invalid EIP-1559 gas envelope")
        to = _hex_address(envelope.executor, "executor")
        unsigned = [
            _rlp_uint(envelope.chain_id),
            _rlp_uint(envelope.nonce),
            _rlp_uint(envelope.max_priority_fee_per_gas),
            _rlp_uint(envelope.max_fee_per_gas),
            _rlp_uint(envelope.gas_limit),
            to,
            b"",  # value = zero
            envelope.calldata,
            [],  # access list
        ]
        signing_payload = b"\x02" + rlp.encode(unsigned)
        digest = bytes.fromhex(keccak256_hex(signing_payload)[2:])
        signature = keys.PrivateKey(bytes.fromhex(self.private_key[2:])).sign_msg_hash(digest)
        signed = unsigned + [_rlp_uint(signature.v), _rlp_uint(signature.r), _rlp_uint(signature.s)]
        return b"\x02" + rlp.encode(signed)


def recover_eip1559_sender(raw_transaction: bytes) -> str:
    """Recover the Ethereum sender from a canonical type-2 signed transaction."""
    if not isinstance(raw_transaction, bytes) or len(raw_transaction) < 2 or raw_transaction[0] != 2:
        raise SignerError("signed transaction must be an EIP-1559 type-2 transaction")
    try:
        fields = rlp.decode(raw_transaction[1:], strict=True)
    except Exception as exc:
        raise SignerError("signed transaction RLP is invalid") from exc
    if len(fields) != 12:
        raise SignerError("signed EIP-1559 transaction must contain exactly twelve fields")

    chain_id, nonce, max_priority, max_fee, gas_limit, to, value, data, access_list, y_parity, r, s = fields
    if not chain_id or len(y_parity) != 1 or y_parity[0] not in (0, 1):
        raise SignerError("invalid EIP-1559 signature framing")
    if len(to) not in (0, 20) or len(r) == 0 or len(s) == 0:
        raise SignerError("invalid EIP-1559 transaction field encoding")
    if len(access_list) < 0:  # defensive type guard, lists always satisfy this
        raise SignerError("invalid access list")

    unsigned = [chain_id, nonce, max_priority, max_fee, gas_limit, to, value, data, access_list]
    digest = bytes.fromhex(keccak256_hex(b"\x02" + rlp.encode(unsigned))[2:])
    try:
        signature = keys.Signature(vrs=(y_parity[0], int.from_bytes(r, "big"), int.from_bytes(s, "big")))
        return signature.recover_public_key_from_msg_hash(digest).to_checksum_address().lower()
    except (BadSignature, ValueError, OverflowError) as exc:
        raise SignerError("EIP-1559 sender recovery failed") from exc


def sign_governed_transaction(
    *,
    signer: TransactionSigner,
    governor: GovernorDecision,
    intent: ExecutionIntent,
    authorization: Authorization,
    envelope: TransactionEnvelope,
    now: int,
) -> SignedTransaction:
    """Sign only an exact, approved, still-authorized transaction envelope."""
    if not governor.approved:
        raise SignerError("governor did not approve signing")
    if now < 0:
        raise SignerError("current time cannot be negative")
    if intent.deadline < now:
        raise SignerError("execution deadline has expired")
    if governor.intent_hash.lower() != intent.intent_hash().lower():
        raise SignerError("governor intent identity does not match current intent")
    if governor.calldata_hash.lower() != envelope.calldata_hash.lower():
        raise SignerError("governor calldata identity does not match envelope")
    if governor.route_hash.lower() != intent.route_hash.lower():
        raise SignerError("governor route identity does not match intent")
    if governor.economic_proof_hash.lower() != intent.economic_proof_hash.lower():
        raise SignerError("governor economic proof identity does not match intent")
    if governor.simulation_proof_hash.lower() != intent.simulation_proof_hash.lower():
        raise SignerError("governor simulation proof identity does not match intent")
    if not authorization.matches_envelope(envelope, now, intent):
        raise SignerError("authorization does not match exact signing envelope")

    signer_address = getattr(signer, "address", None)
    if signer_address is not None:
        if not isinstance(signer_address, str) or signer_address.lower() != intent.sender.lower():
            raise SignerError("signer identity does not match authorized intent sender")

    raw = signer.sign(envelope)
    if not isinstance(raw, bytes) or not raw:
        raise SignerError("signer returned empty or invalid transaction bytes")

    recovered_sender = recover_eip1559_sender(raw)
    if recovered_sender != intent.sender.lower():
        raise SignerError("recovered transaction sender does not match authorized intent sender")

    return SignedTransaction(
        intent_hash=intent.intent_hash(),
        governor_decision_hash=governor.decision_hash,
        transaction_hash=keccak256_hex(raw),
        raw_transaction=raw,
    )
