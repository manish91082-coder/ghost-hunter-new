from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.durable_nonce import (
    DurableNonceInvariantError,
    DurableNonceRecord,
    DurableNonceStore,
    NonceStatus,
)


class DurableNonceTests(unittest.TestCase):
    SENDER = "0x0000000000000000000000000000000000000001"

    def record(self):
        return DurableNonceRecord(self.SENDER, 7, "reservation-7", "0xintent", NonceStatus.RESERVED)

    def test_duplicate_nonce_reservation_rejected(self):
        store = DurableNonceStore()
        store.create(self.record())
        with self.assertRaises(DurableNonceInvariantError):
            store.create(self.record())

    def test_happy_path_reaches_included(self):
        store = DurableNonceStore()
        store.create(self.record())
        store.transition(self.SENDER, 7, NonceStatus.SIGNED)
        store.transition(self.SENDER, 7, NonceStatus.SUBMITTED, tx_hash="0xtx1")
        result = store.transition(self.SENDER, 7, NonceStatus.INCLUDED, tx_hash="0xtx1")
        self.assertEqual(result.status, NonceStatus.INCLUDED)

    def test_submitted_requires_tx_hash(self):
        store = DurableNonceStore()
        store.create(self.record())
        store.transition(self.SENDER, 7, NonceStatus.SIGNED)
        with self.assertRaises(DurableNonceInvariantError):
            store.transition(self.SENDER, 7, NonceStatus.SUBMITTED)

    def test_invalid_skip_is_rejected(self):
        store = DurableNonceStore()
        store.create(self.record())
        with self.assertRaises(DurableNonceInvariantError):
            store.transition(self.SENDER, 7, NonceStatus.INCLUDED, tx_hash="0xtx1")

    def test_replacement_path_is_explicit(self):
        store = DurableNonceStore()
        store.create(self.record())
        store.transition(self.SENDER, 7, NonceStatus.SIGNED)
        store.transition(self.SENDER, 7, NonceStatus.SUBMITTED, tx_hash="0xtx1")
        replaced = store.transition(
            self.SENDER, 7, NonceStatus.REPLACED,
            tx_hash="0xtx2", replacement_of="0xtx1",
        )
        self.assertEqual(replaced.replacement_of, "0xtx1")
        self.assertEqual(replaced.tx_hash, "0xtx2")

    def test_terminal_release_cannot_restart(self):
        store = DurableNonceStore()
        store.create(self.record())
        store.transition(self.SENDER, 7, NonceStatus.RELEASED)
        with self.assertRaises(DurableNonceInvariantError):
            store.transition(self.SENDER, 7, NonceStatus.SIGNED)

    def test_reorg_is_explicit_not_silent_success(self):
        store = DurableNonceStore()
        store.create(self.record())
        store.transition(self.SENDER, 7, NonceStatus.SIGNED)
        store.transition(self.SENDER, 7, NonceStatus.SUBMITTED, tx_hash="0xtx1")
        store.transition(self.SENDER, 7, NonceStatus.INCLUDED, tx_hash="0xtx1")
        result = store.transition(self.SENDER, 7, NonceStatus.REORGED, tx_hash="0xtx1")
        self.assertEqual(result.status, NonceStatus.REORGED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
