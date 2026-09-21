"""Tests for fail-closed transaction chain observation."""

import unittest

from phantomx.chain_observer import ChainEvidence, ChainObservationError, ChainObservationState, observe


class ChainObserverTests(unittest.TestCase):
    def evidence(self, **overrides):
        values = dict(
            tx_hash="0x" + "11" * 32, tx_nonce=5, pending_nonce=5,
            tx_present=True, receipt_present=False, receipt_status=None,
            block_hash=None, block_number=None, canonical_block_hash=None,
            replacement_tx_hash=None,
        )
        values.update(overrides)
        return ChainEvidence(**values)

    def test_pending_transaction_is_pending(self):
        self.assertEqual(observe(self.evidence(tx_present=True)).state, ChainObservationState.PENDING)

    def test_receipt_requires_transaction_presence(self):
        e = self.evidence(tx_present=False, receipt_present=True, receipt_status=1, block_hash="0xblock", block_number=100, canonical_block_hash="0xblock")
        with self.assertRaises(ChainObservationError):
            observe(e)

    def test_receipt_requires_block_identity(self):
        e = self.evidence(receipt_present=True, receipt_status=1)
        self.assertEqual(observe(e).state, ChainObservationState.UNKNOWN)

    def test_replacement_cannot_be_claimed_with_included_receipt(self):
        e = self.evidence(receipt_present=True, receipt_status=1, block_hash="0xblock", block_number=100, canonical_block_hash="0xblock", replacement_tx_hash="0x" + "22" * 32)
        with self.assertRaises(ChainObservationError):
            observe(e)

    def test_invalid_receipt_status_fails_closed(self):
        with self.assertRaises(ChainObservationError):
            observe(self.evidence(receipt_present=True, receipt_status=2, block_hash="0xblock", block_number=100, canonical_block_hash="0xblock"))

    def test_successful_canonical_receipt_is_included(self):
        e = self.evidence(receipt_present=True, receipt_status=1, block_hash="0xblock", block_number=100, canonical_block_hash="0xblock")
        self.assertEqual(observe(e).state, ChainObservationState.INCLUDED)

    def test_reverted_receipt_is_reverted(self):
        e = self.evidence(receipt_present=True, receipt_status=0, block_hash="0xblock", block_number=100, canonical_block_hash="0xblock")
        self.assertEqual(observe(e).state, ChainObservationState.REVERTED)

    def test_noncanonical_receipt_is_reorged(self):
        e = self.evidence(receipt_present=True, receipt_status=1, block_hash="0xold", block_number=100, canonical_block_hash="0xnew")
        self.assertEqual(observe(e).state, ChainObservationState.REORGED)

    def test_missing_tx_without_nonce_advance_is_not_found(self):
        self.assertEqual(observe(self.evidence(tx_present=False, pending_nonce=5)).state, ChainObservationState.NOT_FOUND)

    def test_missing_tx_with_advanced_nonce_proves_drop(self):
        self.assertEqual(observe(self.evidence(tx_present=False, pending_nonce=6)).state, ChainObservationState.DROPPED)

    def test_not_found_without_nonce_is_not_drop_proof(self):
        self.assertEqual(observe(self.evidence(tx_present=False, pending_nonce=None)).state, ChainObservationState.NOT_FOUND)

    def test_explicit_replacement_is_replaced(self):
        replacement = "0x" + "22" * 32
        e = self.evidence(tx_present=True, replacement_tx_hash=replacement)
        d = observe(e)
        self.assertEqual(d.state, ChainObservationState.REPLACED)
        self.assertEqual(d.replacement_tx_hash, replacement)

    def test_negative_nonce_fails_closed(self):
        with self.assertRaises(ChainObservationError):
            observe(self.evidence(tx_nonce=-1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
