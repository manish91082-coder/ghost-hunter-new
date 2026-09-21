# Phase 19 Controlled Signer Evidence Intake

## Purpose
Define the exact non-secret evidence package required to close the controlled production signer-identity P0 gate. This document does not request, store, transmit, or verify any private key material.

## Required evidence package

The controlled external evidence system must preserve, at minimum:

- `schema_version`: integer, currently `1`
- `expected_address`: independently approved production signer address
- `recovered_address`: address recovered from the externally produced signature
- `challenge`: the exact fresh 32-byte challenge used for this proof
- `challenge_hash`: canonical hash corresponding to the challenge
- `signature`: exact 65-byte signature returned by the externally controlled signer
- `evidence_hash`: canonical evidence-record hash produced by the certified verifier
- `verifier_commit`: exact source commit of the verifier used for independent verification
- `certification_ref`: CI certification reference for that verifier implementation
- `operator_identity`: external operator or signing-system identity
- `witness_identity`: independent witness/reviewer identity
- `observed_at_utc`: UTC timestamp recorded by the external evidence system

## Required acceptance chain

`fresh challenge -> external signer -> exactly one signature -> independent verifier -> recovered address == approved address -> provenance captured -> independent review`

All values must be internally consistent. The challenge must be fresh for this proof. The signature must be exactly 65 bytes. The expected and recovered addresses must match after canonical hexadecimal normalization.

## Security boundary

The evidence package must never contain:

- private keys
- seed phrases
- keystore passwords
- hardware-wallet secrets
- relay authentication secrets

A signature is non-secret audit evidence, but it is not a credential substitute and must remain under controlled audit handling.

## P0 gate decision

The production signer-identity gate may become **GREEN** only after the complete package is independently reviewed and accepted. A repository CI pass, a locally generated test signature, or a mechanism-level verifier test is not production identity evidence.

Until acceptance:

- live signing remains BLOCKED
- public broadcast remains BLOCKED
- live capital remains LOCKED
- production readiness remains NOT ACHIEVED
