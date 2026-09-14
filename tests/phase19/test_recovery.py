import unittest

from phantomx.durable_nonce import DurableNonceRecord, DurableNonceStore, NonceStatus
from phantomx.recovery import (
    ChainTransactionObservation,
    ChainTxState,
    RecoveryError,
    decide,
    prove_dropped,
    prove_reorg,
)


SENDER = "0xabc"
TX = "0x1111"


def record(status=NonceStatus.SUBMITTED):
    return DurableNonceRecord(SENDER, 7, "reservation-7", "intent-7", status, TX)


class RecoveryTests(unittest.TestCase):
    def test_pending_holds_state(self):
        decision = decide(current_status=NonceStatus.SUBMITTED, active_tx_hash=TX, observation=ChainTransactionObservation(TX, 7, ChainTxState.PENDING), chain_pending_nonce=7)
        self.assertEqual(decision.action, "HOLD")
        self.assertIsNone(decision.next_status)

    def test_missing_transaction_does_not_imply_drop(self):
        decision = decide(current_status=NonceStatus.SUBMITTED, active_tx_hash=TX, observation=ChainTransactionObservation(TX, 7, ChainTxState.NOT_FOUND), chain_pending_nonce=7)
        self.assertEqual(decision.action, "HOLD")

    def test_successful_receipt_marks_included(self):
        observation = ChainTransactionObservation(TX, 7, ChainTxState.INCLUDED_SUCCESS, block_hash="0xblock", receipt_block_hash="0xblock", gas_used=21000, effective_gas_price=100)
        decision = decide(current_status=NonceStatus.SUBMITTED, active_tx_hash=TX, observation=observation, chain_pending_nonce=8)
        self.assertEqual(decision.next_status, NonceStatus.INCLUDED)

    def test_revert_is_included_but_not_profit_confirmation(self):
        observation = ChainTransactionObservation(TX, 7, ChainTxState.INCLUDED_REVERT, block_hash="0xblock", receipt_block_hash="0xblock", gas_used=50000, effective_gas_price=100)
        decision = decide(current_status=NonceStatus.SUBMITTED, active_tx_hash=TX, observation=observation, chain_pending_nonce=8)
        self.assertEqual(decision.action, "MARK_REVERTED")
        self.assertEqual(decision.next_status, NonceStatus.INCLUDED)

    def test_wrong_hash_cannot_mutate_active_record(self):
        with self.assertRaises(RecoveryError):
            decide(current_status=NonceStatus.SUBMITTED, active_tx_hash=TX, observation=ChainTransactionObservation("0x2222", 7, ChainTxState.PENDING), chain_pending_nonce=7)

    def test_drop_requires_nonce_consumption(self):
        with self.assertRaises(RecoveryError):
            prove_dropped(active_tx_hash=TX, nonce=7, chain_pending_nonce=7, replacement_tx_hash=None)
        decision = prove_dropped(active_tx_hash=TX, nonce=7, chain_pending_nonce=8, replacement_tx_hash="0x2222")
        self.assertEqual(decision.next_status, NonceStatus.DROPPED)

    def test_state_machine_can_apply_drop_after_explicit_proof(self):
        store = DurableNonceStore()
        store.create(record())
        decision = prove_dropped(active_tx_hash=TX, nonce=7, chain_pending_nonce=8, replacement_tx_hash=None)
        updated = store.transition(SENDER, 7, decision.next_status)
        self.assertEqual(updated.status, NonceStatus.DROPPED)

    def test_reorg_requires_changed_canonical_block_and_missing_receipt(self):
        decision = prove_reorg(previously_included_block_hash="0xold", canonical_block_hash="0xnew", receipt_still_present=False)
        self.assertEqual(decision.next_status, NonceStatus.REORGED)

    def test_reorg_without_receipt_disappearance_is_rejected(self):
        with self.assertRaises(RecoveryError):
            prove_reorg(previously_included_block_hash="0xold", canonical_block_hash="0xnew", receipt_still_present=True)

    def test_reorg_can_move_included_record_back_to_reorged(self):
        store = DurableNonceStore()
        store.create(record(NonceStatus.SUBMITTED))
        store.transition(SENDER, 7, NonceStatus.INCLUDED, tx_hash=TX)
        decision = prove_reorg(previously_included_block_hash="0xold", canonical_block_hash="0xnew", receipt_still_present=False)
        updated = store.transition(SENDER, 7, decision.next_status)
        self.assertEqual(updated.status, NonceStatus.REORGED)

    def test_unknown_evidence_holds(self):
        decision = decide(current_status=NonceStatus.SUBMITTED, active_tx_hash=TX, observation=ChainTransactionObservation(TX, 7, ChainTxState.UNKNOWN), chain_pending_nonce=7)
        self.assertEqual(decision.action, "HOLD")


if __name__ == "__main__":
    unittest.main()
