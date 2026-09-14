"""Adversarial tests for the Phase-19 persistent nonce store."""

from __future__ import annotations

import multiprocessing
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

from phantomx.durable_nonce import DurableNonceInvariantError, NonceStatus
from phantomx.sqlite_nonce_store import SQLiteNonceStore


SENDER = "0x00000000000000000000000000000000000000AA"


def _reserve_worker(db_path: str, worker_id: int) -> tuple[str, int | None]:
    store = SQLiteNonceStore(db_path, timeout_seconds=30)
    try:
        record = store.reserve(
            SENDER,
            f"reservation-{worker_id}",
            f"intent-{worker_id}",
            chain_pending_nonce=100,
        )
        return "ok", record.nonce
    except Exception as exc:  # pragma: no cover - diagnostic path
        return type(exc).__name__, None


class SQLiteNonceStoreTests(unittest.TestCase):
    def test_persists_across_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "nonce.db")
            first = SQLiteNonceStore(path)
            reserved = first.reserve(SENDER, "reservation-1", "intent-1", chain_pending_nonce=7)
            first.transition(SENDER, 7, NonceStatus.SIGNED)

            second = SQLiteNonceStore(path)
            restored = second.get(SENDER, 7)
            self.assertEqual(restored, second.get(SENDER, reserved.nonce))
            self.assertEqual(restored.status, NonceStatus.SIGNED)
            self.assertEqual(second.next_nonce(SENDER), 8)

    def test_chain_reconciliation_never_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "nonce.db")
            store = SQLiteNonceStore(path)
            self.assertEqual(store.reconcile_pending_nonce(SENDER, 50), 50)
            self.assertEqual(store.reconcile_pending_nonce(SENDER, 12), 50)
            self.assertEqual(store.reserve(SENDER, "reservation-50", "intent-50").nonce, 50)

    def test_duplicate_reservation_id_is_rejected_without_cursor_advance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "nonce.db")
            store = SQLiteNonceStore(path)
            store.reserve(SENDER, "same-id", "intent-a", chain_pending_nonce=4)
            with self.assertRaises(DurableNonceInvariantError):
                store.reserve(SENDER, "same-id", "intent-b")
            self.assertEqual(store.next_nonce(SENDER), 5)

    def test_replacement_requires_old_transaction_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "nonce.db")
            store = SQLiteNonceStore(path)
            store.reserve(SENDER, "reservation-1", "intent-1", chain_pending_nonce=9)
            store.transition(SENDER, 9, NonceStatus.SIGNED)
            store.transition(SENDER, 9, NonceStatus.SUBMITTED, tx_hash="0xold")
            with self.assertRaises(DurableNonceInvariantError):
                store.transition(SENDER, 9, NonceStatus.REPLACED, tx_hash="0xnew")
            replaced = store.transition(
                SENDER,
                9,
                NonceStatus.REPLACED,
                tx_hash="0xnew",
                replacement_of="0xold",
            )
            self.assertEqual(replaced.tx_hash, "0xnew")
            self.assertEqual(replaced.replacement_of, "0xold")

    def test_invalid_transition_does_not_mutate_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "nonce.db")
            store = SQLiteNonceStore(path)
            store.reserve(SENDER, "reservation-1", "intent-1", chain_pending_nonce=11)
            with self.assertRaises(DurableNonceInvariantError):
                store.transition(SENDER, 11, NonceStatus.INCLUDED, tx_hash="0xbad")
            self.assertEqual(store.get(SENDER, 11).status, NonceStatus.RESERVED)

    def test_concurrent_processes_get_unique_monotonic_nonces(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "nonce.db")
            context = multiprocessing.get_context("spawn")
            with context.Pool(processes=8) as pool:
                results = pool.starmap(
                    _reserve_worker,
                    [(path, worker_id) for worker_id in range(8)],
                )

            failures = [result for result in results if result[0] != "ok"]
            self.assertEqual(failures, [])
            nonces = sorted(result[1] for result in results)
            self.assertEqual(nonces, list(range(100, 108)))

            store = SQLiteNonceStore(path)
            records = list(store.records())
            self.assertEqual([record.nonce for record in records], list(range(100, 108)))
            self.assertEqual(store.next_nonce(SENDER), 108)


if __name__ == "__main__":
    unittest.main(verbosity=2)
