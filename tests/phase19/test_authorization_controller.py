"""Adversarial tests for one-shot authorization control."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.authorization import AuthorizationController
from phantomx.execution import Authorization, ExecutionIntent


class AuthorizationControllerTests(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            137,
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
            "0x0000000000000000000000000000000000000003",
            1_000_000,
            "0xroute",
            "0xcalldata",
            "0xeconomic",
            "0xsimulation",
            42,
            2_000,
        )
        self.authorization = Authorization(
            self.intent.intent_hash(),
            self.intent.calldata_hash,
            self.intent.economic_proof_hash,
            self.intent.simulation_proof_hash,
            self.intent.chain_id,
            self.intent.executor,
            self.intent.sender,
            self.intent.nonce,
            self.intent.deadline,
        )

    def test_matching_authorization_is_consumed_once(self):
        controller = AuthorizationController()
        receipt = controller.authorize(self.authorization, self.intent, now=1_000)
        self.assertEqual(receipt.intent_hash, self.intent.intent_hash())
        self.assertEqual(receipt.nonce, 42)
        self.assertTrue(controller.is_consumed(self.intent.intent_hash()))

        with self.assertRaises(ValueError):
            controller.authorize(self.authorization, self.intent, now=1_001)

    def test_mutated_intent_cannot_be_consumed(self):
        controller = AuthorizationController()
        mutated = self.intent.with_field(loan_amount=2_000_000)
        with self.assertRaises(ValueError):
            controller.authorize(self.authorization, mutated, now=1_000)

    def test_expired_authorization_cannot_be_consumed(self):
        controller = AuthorizationController()
        with self.assertRaises(ValueError):
            controller.authorize(self.authorization, self.intent, now=2_001)

    def test_nonce_must_increase_for_same_sender(self):
        controller = AuthorizationController()
        controller.authorize(self.authorization, self.intent, now=1_000)

        next_intent = self.intent.with_field(nonce=41)
        next_auth = Authorization(
            next_intent.intent_hash(), next_intent.calldata_hash,
            next_intent.economic_proof_hash, next_intent.simulation_proof_hash,
            next_intent.chain_id, next_intent.executor, next_intent.sender,
            next_intent.nonce, next_intent.deadline,
        )
        with self.assertRaises(ValueError):
            controller.authorize(next_auth, next_intent, now=1_000)

    def test_higher_nonce_is_accepted(self):
        controller = AuthorizationController()
        controller.authorize(self.authorization, self.intent, now=1_000)
        next_intent = self.intent.with_field(nonce=43)
        next_auth = Authorization(
            next_intent.intent_hash(), next_intent.calldata_hash,
            next_intent.economic_proof_hash, next_intent.simulation_proof_hash,
            next_intent.chain_id, next_intent.executor, next_intent.sender,
            next_intent.nonce, next_intent.deadline,
        )
        receipt = controller.authorize(next_auth, next_intent, now=1_000)
        self.assertEqual(receipt.nonce, 43)
        self.assertEqual(controller.last_nonce(self.intent.sender), 43)


if __name__ == "__main__":
    unittest.main(verbosity=2)
