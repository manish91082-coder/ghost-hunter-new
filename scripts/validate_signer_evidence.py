#!/usr/bin/env python3
"""Validate a non-secret Phase-19 controlled signer evidence package.

The package contains the fresh challenge, external signature, verifier output,
and external provenance metadata. This utility never accepts private keys,
seed phrases, keystore passwords, or hardware-wallet secrets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from phantomx.signer import SignerError
from phantomx.signer_identity_verifier import verify_signer_identity_proof

_REQUIRED = {
    "schema_version",
    "expected_address",
    "recovered_address",
    "challenge",
    "challenge_hash",
    "signature",
    "evidence_hash",
    "verifier_commit",
    "certification_ref",
    "operator_identity",
    "witness_identity",
    "observed_at_utc",
}


def _hex_bytes(value: object, *, field: str, size: int) -> bytes:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be hexadecimal text")
    text = value[2:] if value.startswith("0x") else value
    if len(text) != size * 2:
        raise ValueError(f"{field} must encode exactly {size} bytes")
    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        raise ValueError(f"{field} is not valid hexadecimal") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate controlled Phase-19 signer evidence")
    parser.add_argument("evidence_file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        record = json.loads(args.evidence_file.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("evidence package must be a JSON object")
        missing = sorted(_REQUIRED - set(record))
        if missing:
            raise ValueError("missing required evidence fields: " + ", ".join(missing))
        if set(record) - _REQUIRED:
            raise ValueError("evidence package contains unknown fields")
        if record["schema_version"] != 1:
            raise ValueError("unsupported evidence schema version")
        for field in ("verifier_commit", "certification_ref", "operator_identity", "witness_identity", "observed_at_utc", "evidence_hash", "challenge_hash"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ValueError(f"{field} must be non-empty text")

        challenge = _hex_bytes(record["challenge"], field="challenge", size=32)
        signature = _hex_bytes(record["signature"], field="signature", size=65)
        evidence = verify_signer_identity_proof(
            expected_address=record["expected_address"],
            challenge=challenge,
            signature=signature,
        )
        if evidence.recovered_address.lower() != str(record["recovered_address"]).lower():
            raise ValueError("recovered address does not match verifier result")
        if evidence.challenge_hash.lower() != str(record["challenge_hash"]).lower():
            raise ValueError("challenge hash does not match verifier result")
        if evidence.evidence_hash.lower() != str(record["evidence_hash"]).lower():
            raise ValueError("evidence hash does not match verifier result")
    except (OSError, json.JSONDecodeError, ValueError, SignerError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "schema_version": 1,
        "status": "ACCEPTED_FOR_INDEPENDENT_REVIEW",
        "expected_address": evidence.expected_address,
        "recovered_address": evidence.recovered_address,
        "challenge_hash": evidence.challenge_hash,
        "evidence_hash": evidence.evidence_hash,
        "verifier_commit": record["verifier_commit"],
        "certification_ref": record["certification_ref"],
        "operator_identity": record["operator_identity"],
        "witness_identity": record["witness_identity"],
        "observed_at_utc": record["observed_at_utc"],
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
