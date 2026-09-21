# Phase 19 Controlled Private Relay Evidence Intake

## Objective
Define the non-secret evidence required to close the controlled production private-relay P0 gate.

This evidence package proves configuration identity and a controlled observation of the approved private-relay boundary. It does not contain private keys, seed phrases, relay credentials, authorization headers, signed transactions, raw transactions, transaction hashes, or live capital information.

## Required evidence

```json
{
  "schema_version": 1,
  "relay_name": "<approved relay identity>",
  "endpoint_scheme": "https",
  "private_assertion": true,
  "authentication_configured": true,
  "observed_response_class": "<controlled non-secret response classification>",
  "observed_at_utc": "<external timestamp>",
  "operator_identity": "<external operator identity>",
  "witness_identity": "<independent witness identity>",
  "evidence_hash": "0x..."
}
```

The values above are schema placeholders only. They are not production evidence.

## Acceptance chain

1. Operator freezes the approved relay identity and endpoint policy.
2. Endpoint is HTTPS with no embedded credentials.
3. Relay is explicitly asserted private.
4. Authentication is configured externally; authentication material remains outside the evidence package.
5. Controlled observation occurs in an isolated environment with no public fallback.
6. Only non-secret response classification is retained.
7. Canonical evidence hash is computed.
8. Operator and independent witness provenance are retained.
9. Repository validator accepts the package.
10. Independent review confirms the external approval and observation provenance.

## Automatic BLOCK conditions

- non-HTTPS endpoint
- embedded URL credentials
- `private_assertion != true`
- authentication material included in evidence
- private key / seed phrase / keystore password included
- raw transaction or signed transaction included
- transaction hash included as relay-proof evidence
- public or fork relay substituted for the approved private relay
- public fallback path asserted or available for this gate
- empty/missing provenance
- evidence hash mismatch
- unknown schema fields

## Boundary rule

Repository validation establishes internal evidence consistency only. It does not establish that the external endpoint was genuinely approved or that authentication succeeded in production. Those facts require controlled external observation and independent review.

## Prohibited actions during this gate

- no live transaction signing
- no live transaction submission
- no public broadcast
- no capital release
- no public-RPC fallback
