#!/usr/bin/env python3
"""Package verified non-secret signer output into the Phase-19 intake schema.

This utility never accepts a private key. It consumes only the verifier's
non-secret JSON output plus externally supplied provenance metadata.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence

from phantomx.hashing import keccak256_hex

_HEX32_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_HEX65_RE = re.compile(r"^0x[0-9a-fA-F]{130}$")
_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_HASH_RE = _HEX32_RE
_REQUIRED_VERIFIER = {
    "schema_version",
    "expected_address",
    "recovered_address",
    "challenge_hash",
    "signature",
    "evidence_hash",
}


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _match(value: Any, pattern: re.Pattern[str], field: str) -> str:
    text = _text(value, field)
    if not pattern.fullmatch(text):
        raise ValueError(f"{field} has invalid format")
    return text.lower()


def _load_verifier_output(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("verifier output must be a JSON object")
    if set(record) != _REQUIRED_VERIFIER:
        raise ValueError("verifier output fields do not match the certified output schema")
    if record["schema_version"] != 1:
        raise ValueError("unsupported verifier output schema version")
    expected = _match(record["expected_address"], _ADDR_RE, "expected_address")
    recovered = _match(record["recovered_address"], _ADDR_RE, "recovered_address")
    if expected != recovered:
        raise ValueError("recovered_address does not match expected_address")
    challenge_hash = _match(record["challenge_hash"], _HASH_RE, "challenge_hash")
    signature = _match(record["signature"], _HEX65_RE, "signature")
    evidence_hash = _match(record["evidence_hash"], _HASH_RE, "evidence_hash")
    return {
        **record,
        "expected_address": expected,
        "recovered_address": recovered,
        "challenge_hash": challenge_hash,
        "signature": signature,
        "evidence_hash": evidence_hash,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package Phase-19 signer verifier output")
    parser.add_argument("verifier_output", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("--challenge", required=True, help="fresh 32-byte challenge used by the external signer")
    parser.add_argument("--verifier-commit", required=True, help="exact verifier source commit")
    parser.add_argument("--certification-ref", required=True, help="CI certification reference for the verifier")
    parser.add_argument("--operator-identity", required=True)
    parser.add_argument("--witness-identity", required=True)
    parser.add_argument("--observed-at-utc", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        verifier = _load_verifier_output(args.verifier_output)
        challenge = _match(args.challenge, _HEX32_RE, "challenge")
        expected_challenge_hash = keccak256_hex(bytes.fromhex(challenge[2:]))
        if verifier["challenge_hash"] != expected_challenge_hash:
            raise ValueError("challenge does not match verifier challenge_hash")
        expected_evidence_hash = keccak256_hex(
            (verifier["challenge_hash"] + verifier["recovered_address"]).encode("ascii")
        )
        if verifier["evidence_hash"] != expected_evidence_hash:
            raise ValueError("evidence_hash does not match verifier challenge/address")

        package = {
            "schema_version": 1,
            "expected_address": verifier["expected_address"],
            "recovered_address": verifier["recovered_address"],
            "challenge": challenge,
            "challenge_hash": verifier["challenge_hash"],
            "signature": verifier["signature"],
            "evidence_hash": verifier["evidence_hash"],
            "verifier_commit": _text(args.verifier_commit, "verifier_commit"),
            "certification_ref": _text(args.certification_ref, "certification_ref"),
            "operator_identity": _text(args.operator_identity, "operator_identity"),
            "witness_identity": _text(args.witness_identity, "witness_identity"),
            "observed_at_utc": _text(args.observed_at_utc, "observed_at_utc"),
        }
        args.output_file.write_text(json.dumps(package, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({"status": "PACKAGED_FOR_PHASE19_INTAKE", "output_file": str(args.output_file)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
