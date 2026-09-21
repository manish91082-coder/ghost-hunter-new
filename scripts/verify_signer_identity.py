#!/usr/bin/env python3
"""Operator-safe Phase-19 production signer identity evidence utility.

This utility never accepts or handles a private key. It can generate a fresh
32-byte challenge for an external signer and verify a returned 65-byte
signature against the expected Ethereum address. Successful verification
prints a canonical JSON evidence record suitable for an audit log.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from typing import Sequence

from phantomx.signer import SignerError
from phantomx.signer_identity_verifier import verify_signer_identity_proof


def _parse_hex_bytes(value: str, *, field: str, size: int) -> bytes:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be hex text")
    text = value[2:] if value.startswith("0x") else value
    if len(text) != size * 2:
        raise ValueError(f"{field} must encode exactly {size} bytes")
    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        raise ValueError(f"{field} is not valid hexadecimal") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or independently verify Phase-19 non-secret signer identity evidence."
    )
    parser.add_argument("--expected-address", help="expected Ethereum signer address (0x + 40 hex chars)")
    parser.add_argument("--challenge", help="exact 32-byte challenge as hexadecimal")
    parser.add_argument("--signature", help="external signer's exact 65-byte secp256k1 signature as hexadecimal")
    parser.add_argument(
        "--generate-challenge",
        action="store_true",
        help="generate a cryptographically random 32-byte challenge and print only its hex value",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.generate_challenge:
        if args.expected_address or args.challenge or args.signature:
            parser.error("--generate-challenge cannot be combined with verification arguments")
        print("0x" + secrets.token_bytes(32).hex())
        return 0

    missing = [name for name, value in (
        ("--expected-address", args.expected_address),
        ("--challenge", args.challenge),
        ("--signature", args.signature),
    ) if value is None]
    if missing:
        parser.error("verification requires " + ", ".join(missing))

    try:
        challenge = _parse_hex_bytes(args.challenge, field="challenge", size=32)
        signature = _parse_hex_bytes(args.signature, field="signature", size=65)
        evidence = verify_signer_identity_proof(
            expected_address=args.expected_address,
            challenge=challenge,
            signature=signature,
        )
    except (ValueError, SignerError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    record = {
        "schema_version": 1,
        "expected_address": evidence.expected_address,
        "recovered_address": evidence.recovered_address,
        "challenge_hash": evidence.challenge_hash,
        "signature": "0x" + evidence.signature.hex(),
        "evidence_hash": evidence.evidence_hash,
    }
    print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
