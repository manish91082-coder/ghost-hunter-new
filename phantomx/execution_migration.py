"""Validated migration planning from legacy Phase-19 stores.

Migration is intentionally plan-only. It reads legacy SQLite databases and
produces deterministic records to import into the unified store. It never
silently overwrites conflicts and never performs execution actions.
"""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class MigrationItem:
    kind: str
    identity: str
    payload: tuple[object, ...]


class MigrationConflict(RuntimeError):
    pass


def _rows(path: str, query: str) -> list[tuple[object, ...]]:
    with sqlite3.connect(path) as db:
        return db.execute(query).fetchall()


def inspect_legacy_nonce_store(path: str) -> tuple[MigrationItem, ...]:
    """Read the known legacy nonce schema without mutating it."""
    rows = _rows(
        path,
        "SELECT sender,nonce,reservation_id,intent_hash,status,tx_hash,replacement_of "
        "FROM nonce_records ORDER BY sender,nonce",
    )
    return tuple(MigrationItem("nonce", f"{r[0]}:{r[1]}", r) for r in rows)


def inspect_legacy_transaction_store(path: str) -> tuple[MigrationItem, ...]:
    """Read the known legacy transaction schema without mutating it."""
    rows = _rows(
        path,
        "SELECT record_hash,intent_hash,authorization_hash,reservation_id,chain_id,sender,executor,nonce,"
        "calldata_hash,gas_limit,max_fee_per_gas,max_priority_fee_per_gas,tx_hash,state,replacement_of "
        "FROM transaction_records ORDER BY record_hash",
    )
    return tuple(MigrationItem("transaction", str(r[0]), r) for r in rows)


def inspect_legacy_journal(path: str) -> tuple[MigrationItem, ...]:
    """Read the known legacy recovery journal without mutating it."""
    rows = _rows(
        path,
        "SELECT sequence,record_hash,action,chain_state,tx_hash,replacement_tx_hash,reason,applied "
        "FROM recovery_journal ORDER BY sequence",
    )
    return tuple(MigrationItem("journal", str(r[0]), r) for r in rows)


def validate_migration_inputs(
    nonce_items: tuple[MigrationItem, ...],
    transaction_items: tuple[MigrationItem, ...],
    journal_items: tuple[MigrationItem, ...],
) -> None:
    """Fail closed on identity conflicts before any import is attempted."""
    nonce_by_key: dict[str, MigrationItem] = {}
    for item in nonce_items:
        if item.identity in nonce_by_key and nonce_by_key[item.identity].payload != item.payload:
            raise MigrationConflict(f"conflicting nonce identity: {item.identity}")
        nonce_by_key[item.identity] = item

    tx_hashes: set[str] = set()
    tx_identities: set[str] = set()
    for item in transaction_items:
        if item.identity in tx_identities:
            raise MigrationConflict(f"duplicate transaction identity: {item.identity}")
        tx_identities.add(item.identity)
        tx_hash = str(item.payload[12]).lower()
        if tx_hash in tx_hashes:
            raise MigrationConflict(f"duplicate transaction hash: {tx_hash}")
        tx_hashes.add(tx_hash)
        sender = str(item.payload[5]).lower()
        nonce = int(item.payload[7])
        key = f"{sender}:{nonce}"
        nonce_item = nonce_by_key.get(key)
        if nonce_item is None:
            raise MigrationConflict(f"transaction {item.identity} has no matching nonce record")
        if str(nonce_item.payload[2]) != str(item.payload[3]):
            raise MigrationConflict(f"reservation mismatch for transaction {item.identity}")
        if str(nonce_item.payload[3]).lower() != str(item.payload[1]).lower():
            raise MigrationConflict(f"intent mismatch for transaction {item.identity}")

    journal_keys: set[tuple[str, str, str]] = set()
    for item in journal_items:
        record_hash, _, action, _, tx_hash = item.payload[:5]
        key = (str(record_hash).lower(), str(tx_hash).lower(), str(action))
        if key in journal_keys:
            raise MigrationConflict(f"duplicate journal identity: {key}")
        journal_keys.add(key)


def build_migration_manifest(
    nonce_items: tuple[MigrationItem, ...],
    transaction_items: tuple[MigrationItem, ...],
    journal_items: tuple[MigrationItem, ...],
) -> tuple[MigrationItem, ...]:
    """Return a deterministic, validated, import-ready manifest."""
    validate_migration_inputs(nonce_items, transaction_items, journal_items)
    return tuple(nonce_items) + tuple(transaction_items) + tuple(journal_items)
