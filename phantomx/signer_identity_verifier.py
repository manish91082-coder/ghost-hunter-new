"""Verify non-secret signer identity evidence without private-key access.

This module is deliberately verifier-only. It accepts an externally produced
challenge signature, recovers the Ethereum address, and rebuilds the immutable
proof record used by the Phase-19 signer boundary. No private key, RPC, relay,
or transaction broadcast is involved.
"""
from __future__ import annotations

from eth_keys import keys
from eth_keys.exceptions import BadSignature

from .hashing import keccak256_hex
from .signer import SignedChallenge, SignerError, _hex_address


def verify_signer_identity_proof(
    *,
    expected_address: str,
    challenge: bytes,
    signature: bytes,
) -> SignedChallenge:
    """Verify externally supplied signer-control evidence.

    The verifier does not need access to the signer or its private key. It
    recovers the address from the canonical 65-byte signature over the exact
    32-byte challenge and requires an exact match with ``expected_address``.
    """
    expected = expected_address.lower() if isinstance(expected_address, str) else expected_address
    _hex_address(expected, "expected_address")
    if not isinstance(challenge, bytes) or len(challenge) != 32:
        raise SignerError("challenge must be exactly 32 bytes")
    if not isinstance(signature, bytes) or len(signature) != 65:
        raise SignerError("challenge signature must be exactly 65 bytes")

    try:
        recovered = (
            keys.Signature(signature_bytes=signature)
            .recover_public_key_from_msg_hash(challenge)
            .to_checksum_address()
            .lower()
        )
    except (BadSignature, ValueError, OverflowError) as exc:
        raise SignerError("signer challenge recovery failed") from exc

    if recovered != expected:
        raise SignerError("signer challenge identity does not match expected address")

    challenge_hash = keccak256_hex(challenge)
    evidence_hash = keccak256_hex((challenge_hash + recovered).encode("ascii"))
    return SignedChallenge(
        challenge_hash=challenge_hash,
        expected_address=expected,
        recovered_address=recovered,
        signature=signature,
        evidence_hash=evidence_hash,
    )
