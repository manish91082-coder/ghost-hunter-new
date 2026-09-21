"""Canonical hashing boundary for PhantomX execution data.

This module is intentionally small. Ethereum-compatible Keccak-256 must be
used for production authorization and calldata binding. Python's hashlib
sha3_256 is NOT interchangeable with Ethereum Keccak-256.

The implementation prefers an installed Ethereum-compatible backend and fails
closed when none is available. It never silently substitutes SHA-256 or NIST
SHA-3 for Ethereum hashing.
"""

from __future__ import annotations

from typing import Union

BytesLike = Union[bytes, bytearray, memoryview]


class KeccakUnavailable(RuntimeError):
    """Raised when no Ethereum Keccak-256 implementation is available."""


def keccak256(data: BytesLike) -> bytes:
    """Return the Ethereum Keccak-256 digest, or fail closed."""
    raw = bytes(data)

    try:
        from Crypto.Hash import keccak  # type: ignore
    except ImportError as exc:
        raise KeccakUnavailable(
            "Ethereum Keccak-256 backend unavailable; refusing a SHA-3 fallback"
        ) from exc

    hasher = keccak.new(digest_bits=256)
    hasher.update(raw)
    return hasher.digest()


def keccak256_hex(data: BytesLike) -> str:
    """Return an Ethereum Keccak-256 digest as a 0x-prefixed hex string."""
    return "0x" + keccak256(data).hex()
