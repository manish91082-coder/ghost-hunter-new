# Phase-19 Realized PnL Provenance Gate

## Purpose

Define the minimum non-secret provenance contract for realized-PnL evidence so that arithmetic validation is not mistaken for proof of an actual settlement.

This document does not authorize live execution, signing, broadcasting, or capital release.

## Required distinction

`economic arithmetic PASS` is not equivalent to `realized settlement PROOF`.

A lane can be accepted by the offline validator only for independent review. It becomes a production gate only after an external, controlled settlement record is independently reviewed and bound to the same immutable artifact/session.

## Required evidence chain

```text
external settlement source
→ settlement evidence identity
→ execution evidence identity
→ immutable artifact binding
→ exact gross result
→ exact gas/loan/DEX/relay/other costs
→ exact realized net result
→ strict net > $0.20
→ operator + witness provenance
→ independent review
```

## Non-secret boundary

The repository evidence package must not contain private keys, seed phrases, keystore passwords, relay credentials, raw signed transactions, authentication secrets, or other prohibited secret material.

The source evidence may remain in an independently controlled system. The repository package should retain only non-secret identities, hashes, normalized accounting fields, and provenance required for independent review.

## Hard gate

The offline validator proves only:

- schema completeness and type constraints;
- arithmetic consistency using exact decimal arithmetic;
- artifact identity format;
- provenance presence;
- canonical evidence hash integrity;
- strict `realized_net_profit_usd > 0.20`.

It does not prove that the external settlement actually occurred. That fact must be independently established from the controlled external evidence source.

## Production rule

No amount of repository CI, fork testing, simulated settlement, or self-authored evidence hash may substitute for controlled external realized-settlement evidence.
