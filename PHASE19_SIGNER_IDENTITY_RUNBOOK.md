# Phase 19 Production Signer Identity Proof Runbook

## Purpose

Establish control of the intended production Ethereum signer without disclosing, transmitting, or storing the private key in the repository, CI logs, chat, or evidence files.

This procedure proves key control only. It does not authorize live signing, transaction broadcast, capital release, or production execution.

## Preconditions

- The intended production signer address is known and independently approved.
- The production signing device/service holds the private key outside the repository.
- The verifier is run from a trusted checkout of the certified Phase-19 branch.
- No private key, seed phrase, keystore password, or hardware-wallet secret is entered into the verifier.

## Procedure

### 1. Generate a fresh challenge

```bash
python scripts/verify_signer_identity.py --generate-challenge
```

Record the single emitted `0x`-prefixed 32-byte challenge in the controlled evidence workspace. Do not reuse an old challenge for a new proof.

### 2. Sign externally

Using the intended production signer, produce exactly one ECDSA/secp256k1 signature over the exact 32-byte challenge. The signing system must not send its private key to the verifier or repository.

The returned signature must be exactly 65 bytes including the recovery identifier expected by the verifier.

### 3. Independently verify

```bash
python scripts/verify_signer_identity.py \
  --expected-address '<APPROVED_PRODUCTION_ADDRESS>' \
  --challenge '<CHALLENGE_HEX>' \
  --signature '<SIGNATURE_HEX>'
```

A successful invocation emits one canonical JSON record. A mismatch or malformed input must fail closed with `BLOCKED:` and no success record.

### 4. Preserve evidence

The controlled evidence record should preserve:

- schema version
- expected signer address
- recovered signer address
- challenge hash
- signature
- evidence hash
- operator/witness identity in the external evidence system
- UTC observation timestamp in the external evidence system
- verifier source commit and CI certification reference

The repository must not be modified with private key material. The raw signature is non-secret but should be handled as audit evidence rather than as a credential.

## Acceptance criteria

The signer identity P0 gate may become GREEN only when all of the following are independently evidenced:

1. The expected address is the intended production signer address.
2. The challenge is fresh and exactly 32 bytes.
3. Exactly one signature was obtained from the externally held production signer.
4. The signature is exactly 65 bytes and recovers to the expected address.
5. Verification was performed by the certified verifier without access to the private key.
6. The resulting evidence record is preserved with provenance.

A CI pass for the mechanism alone is not production identity evidence.

## Failure handling

Any address mismatch, challenge mutation, signature mutation, malformed signature, stale challenge, provenance gap, or uncertainty is `BLOCKED`. Generate a new challenge rather than attempting to repair or reinterpret failed evidence.

## Explicit non-goals

This runbook does not:

- request or accept private keys
- create a production transaction
- broadcast a transaction
- contact a private relay
- release live capital
- mark the production signer gate GREEN automatically

## Next gate

After the signer identity evidence is independently accepted, execute the controlled Polygon provider-authority procedure using explicitly approved endpoints, the intended deployed executor address, common-block evidence, owner binding, and runtime-code identity quorum. Live capital remains locked until every P0 gate is GREEN.
