# Phase 19 Controlled Production Polygon Authority Evidence Intake

## Purpose
Define the exact non-secret evidence package required to close the controlled production Polygon provider-authority P0 gate. This contract proves observation authority for the intended deployed executor; it does not authorize signing, submission, broadcast, or capital release.

## Required evidence package

The controlled external evidence system must preserve, at minimum:

- `schema_version`: integer, currently `1`
- `chain_id`: must be Polygon `137`
- `executor`: intended deployed executor address
- `expected_signer`: independently approved production signer address
- `common_block`: one common block used for all attesting provider observations
- `observed_owner`: executor `owner()` observed at `common_block`
- `runtime_code_hash`: Keccak-256 hash of non-empty deployed runtime bytecode at `common_block`
- `quorum`: required minimum attesting provider count
- `attesting_provider_names`: unique approved provider identities contributing to the quorum
- `provider_observations`: per-provider non-secret observation records containing provider identity, chain id, observed block, owner, and runtime code hash
- `evidence_hash`: canonical evidence-record hash
- `observed_at_utc`: timestamp recorded by the external evidence system
- `operator_identity`: external operator or observation-system identity
- `witness_identity`: independent witness/reviewer identity

## Required acceptance chain

`approved HTTPS providers -> Polygon chainId=137 -> common-block selection -> owner() observation -> runtime-code observation -> quorum agreement -> owner == expected signer -> immutable evidence hash -> provenance -> independent review`

All attesting providers must be unique approved identities. Every provider observation must agree on chain identity, executor, common block, owner, and runtime-code hash. The quorum must be reached without ambiguous competing observations.

## Security boundary

The evidence package must never contain:

- private keys
- seed phrases
- keystore passwords
- relay authentication secrets
- access tokens or authorization headers

Provider endpoint URLs and authentication material belong to the controlled external configuration/evidence system. Do not embed credentials in the evidence package.

## P0 gate decision

The production Polygon authority gate may become **GREEN** only after the complete package is independently reviewed and accepted and the observer-derived evidence is shown to originate from explicitly approved production endpoints.

A public RPC response, a single-provider observation, a fork test, or repository-only configuration is not production authority proof.

Until acceptance:

- production authority remains BLOCKED
- live signing remains BLOCKED
- public broadcast remains BLOCKED
- live capital remains LOCKED
- production readiness remains NOT ACHIEVED
