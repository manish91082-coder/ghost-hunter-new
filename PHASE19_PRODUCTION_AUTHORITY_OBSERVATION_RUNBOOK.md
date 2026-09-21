# Phase 19 Controlled Production Polygon Authority Observation Runbook

## Objective

Produce the external, non-secret evidence required to close the controlled production Polygon provider-authority P0 gate. This procedure is observation-only. It does not sign, submit, broadcast, release capital, or authorize live execution.

## Preconditions

1. The intended production chain is Polygon mainnet, chain ID `137`.
2. The intended deployed executor address is explicitly approved by the operator.
3. The expected production signer address is explicitly approved by the operator.
4. A quorum policy is explicitly approved before observation begins.
5. Each attesting provider is an explicitly approved HTTPS Polygon RPC endpoint.
6. Provider credentials, API tokens, relay credentials, private keys, seed phrases, and keystore passwords remain in the external secret/configuration system and never enter this repository or the evidence package.
7. The observation environment is isolated from transaction-signing and transaction-submission capabilities.

## Procedure

### 1. Freeze the observation inputs

Record the approved executor address, expected signer address, provider identities, quorum value, observer identity, witness identity, and UTC start time. Do not change these inputs during one evidence run.

### 2. Validate provider endpoints

For every approved provider, require HTTPS and reject embedded credentials in the URL. Do not substitute a public or fork-only endpoint because it is reachable or convenient.

### 3. Establish chain identity

For every provider, read `eth_chainId`. Every attesting provider must report Polygon chain ID `137`. Any mismatch blocks the run.

### 4. Select the common observation block

Read `eth_blockNumber` from every provider. Select the minimum reported block as the common block so every provider attests against a block that all providers can observe. If a provider cannot read that block consistently, the run is blocked.

### 5. Observe executor ownership

At the common block, call the intended executor's `owner()` using the selector `0x8da5cb5b`. Require a canonical 32-byte ABI address word and record the observed owner.

### 6. Observe deployed runtime code

At the same common block, call `eth_getCode` for the intended executor. Require non-empty, valid bytecode and compute its Keccak-256 hash. Record the runtime-code hash.

### 7. Require quorum agreement

Every attesting observation must agree on chain ID, common block, executor identity, observed owner, and runtime-code hash. A competing observation set of equal strength is ambiguous and blocks acceptance.

### 8. Verify owner-to-signer binding

Require exact equality between the observed executor owner and the explicitly approved expected signer address. A mismatch blocks the production authority gate.

### 9. Construct the non-secret evidence package

Populate `PHASE19_PRODUCTION_AUTHORITY_EVIDENCE_INTAKE.md` fields exactly. Include one observation record per attesting provider. Compute the canonical evidence hash from the authority evidence fields using the repository's authority model. Preserve the external observation timestamp and operator/witness identities.

### 10. Offline validation

Run the repository validator:

```text
python scripts/validate_production_authority_evidence.py <evidence-file.json>
```

Expected acceptance state is `ACCEPTED_FOR_INDEPENDENT_REVIEW`. Any `BLOCKED` result invalidates the package for this gate.

### 11. Independent review

A witness independent of the observation operator reviews the complete non-secret evidence package, confirms provider identities and provenance against the controlled external system, and confirms that no secret material is present.

### 12. Gate decision

Only after independent acceptance may the production Polygon authority gate be marked GREEN. Even then, signer identity, private relay, shadow/staging, realized PnL, independent final re-audit, and live-capital gates remain separately locked until independently evidenced.

## Required evidence record shape

```json
{
  "schema_version": 1,
  "chain_id": 137,
  "executor": "0x...",
  "expected_signer": "0x...",
  "common_block": 0,
  "observed_owner": "0x...",
  "runtime_code_hash": "0x...",
  "quorum": 0,
  "attesting_provider_names": ["provider-a", "provider-b"],
  "provider_observations": [
    {
      "provider_name": "provider-a",
      "chain_id": 137,
      "observed_block": 0,
      "owner": "0x...",
      "runtime_code_hash": "0x..."
    }
  ],
  "evidence_hash": "0x...",
  "observed_at_utc": "<external timestamp>",
  "operator_identity": "<external operator identity>",
  "witness_identity": "<independent witness identity>"
}
```

The values above are schema placeholders only. They are not production evidence and must never be interpreted as observed values.

## Automatic BLOCK conditions

- any provider is not explicitly approved
- any endpoint is not HTTPS
- embedded URL credentials are present
- any provider reports a chain other than `137`
- common block cannot be established
- provider observations use different blocks
- executor ownership observations disagree
- runtime-code hashes disagree
- quorum is not reached
- competing observations are ambiguous
- observed owner differs from expected signer
- evidence hash does not validate
- provenance or witness identity is missing
- any private key, seed phrase, keystore password, access token, relay secret, or authorization header appears in the evidence package
- evidence originates only from a public/fork endpoint or repository fixture

## Prohibited actions during this gate

- no transaction signing
- no transaction submission
- no public broadcast
- no private-relay send
- no live capital deployment
- no change to deployed executor ownership
- no use of a production private key inside the observation environment

## Evidence provenance

The repository validator establishes internal consistency. It does not by itself prove that an endpoint was approved or that the observed values came from an actual production environment. Those provenance facts must be established by the controlled external observation record and independent review.
