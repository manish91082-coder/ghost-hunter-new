"""Adversarial tests for the Phase-19 nonce policy model."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.nonce_manager import NonceManager


class NonceManagerTests(unittest.TestCase):
    SENDER = "0x0000000000000000000000000000000000000001"

    def test_reservations_are_unique_and_monotonic(self):
        manager = NonceManager(10)
        a = manager.reserve(self.SENDER, "r-a")
        b = manager.reserve(self.SENDER, "r-b")
        c = manager.reserve(self.SENDER, "r-c")
        self.assertEqual([a.nonce, b.nonce, c.nonce], [10, 11, 12])
        self.assertEqual(manager.next_nonce, 13)

    def test_reservation_id_is_single_use(self):
        manager = NonceManager(10)
        manager.reserve(self.SENDER, "r-a")
        with self.assertRaises(ValueError):
            manager.reserve(self.SENDER, "r-a")

    def test_chain_pending_nonce_can_advance_allocator(self):
        manager = NonceManager(10)
        manager.reconcile_pending_nonce(25)
        self.assertEqual(manager.next_nonce, 25)
        self.assertEqual(manager.reserve(self.SENDER, "r-a").nonce, 25)

    def test_chain_nonce_cannot_move_allocator_backwards(self):
        manager = NonceManager(10)
        manager.reserve(self.SENDER, "r-a")
        manager.reconcile_pending_nonce(5)
        self.assertEqual(manager.next_nonce, 11)

    def test_negative_nonce_inputs_rejected(self):
        with self.assertRaises(ValueError):
            NonceManager(-1)
        manager = NonceManager(0)
        with self.assertRaises(ValueError):
            manager.reconcile_pending_nonce(-1)

    def test_unknown_reservation_rejected(self):
        manager = NonceManager(0)
        with self.assertRaises(KeyError):
            manager.reservation("missing")

    def test_distinct_senders_do_not_share_reservation_identity(self):
        manager = NonceManager(0)
        a = manager.reserve(self.SENDER, "r-a")
        b = manager.reserve("0x0000000000000000000000000000000000000002", "r-b")
        self.assertNotEqual(a.reservation_id, b.reservation_id)
        self.assertEqual(a.nonce, 0)
        self.assertEqual(b.nonce, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
