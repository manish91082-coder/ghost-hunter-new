"""Adversarial tests for one-shot authorization and envelope binding."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phantomx.authorization import AuthorizationController
from phantomx.execution import Authorization, ExecutionIntent, TransactionEnvelope


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
            500_000,
            100,
            30,
        )
        self.envelope = TransactionEnvelope(
            self.intent.chain_id,
            self.intent.sender,
            self.intent.executor,
            self.intent.nonce,
            b"phase19-calldata",
            500_000,
            100,
            30,
        )
        self.authorization = replace(self.authorization, calldata_hash=self.envelope.calldata_hash)
        self.intent = self.intent.with_field(calldata_hash=self.envelope.calldata_hash)
        self.authorization = replace(self.authorization, intent_hash=self.intent.intent_hash())

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
        next_auth = replace(
            self.authorization,
            intent_hash=next_intent.intent_hash(),
            nonce=next_intent.nonce,
        )
        with self.assertRaises(ValueError):
            controller.authorize(next_auth, next_intent, now=1_000)

    def test_higher_nonce_is_accepted(self):
        controller = AuthorizationController()
        controller.authorize(self.authorization, self.intent, now=1_000)
        next_intent = self.intent.with_field(nonce=43)
        next_auth = replace(
            self.authorization,
            intent_hash=next_intent.intent_hash(),
            nonce=next_intent.nonce,
        )
        receipt = controller.authorize(next_auth, next_intent, now=1_000)
        self.assertEqual(receipt.nonce, 43)
        self.assertEqual(controller.last_nonce(self.intent.sender), 43)

    def test_exact_envelope_is_accepted_and_consumed(self):
        controller = AuthorizationController()
        receipt = controller.authorize_envelope(self.authorization, self.intent, self.envelope, now=1_000)
        self.assertEqual(receipt.nonce, 42)
        self.assertTrue(controller.is_consumed(self.intent.intent_hash()))

    def test_calldata_mutation_rejected_without_consuming(self):
        controller = AuthorizationController()
        mutated = replace(self.envelope, calldata=b"tampered")
        with self.assertRaises(ValueError):
            controller.authorize_envelope(self.authorization, self.intent, mutated, now=1_000)
        self.assertFalse(controller.is_consumed(self.intent.intent_hash()))

    def test_chain_sender_executor_nonce_mutations_rejected(self):
        controller = AuthorizationController()
        mutations = [
            replace(self.envelope, chain_id=1),
            replace(self.envelope, sender="0x0000000000000000000000000000000000000009"),
            replace(self.envelope, executor="0x0000000000000000000000000000000000000009"),
            replace(self.envelope, nonce=43),
        ]
        for mutated in mutations:
            with self.subTest(mutated=mutated):
                with self.assertRaises(ValueError):
                    controller.authorize_envelope(self.authorization, self.intent, mutated, now=1_000)
        self.assertFalse(controller.is_consumed(self.intent.intent_hash()))

    def test_gas_fields_are_authorization_bound(self):
        controller = AuthorizationController()
        mutations = [
            replace(self.envelope, gas_limit=500_001),
            replace(self.envelope, max_fee_per_gas=101),
            replace(self.envelope, max_priority_fee_per_gas=31),
        ]
        for mutated in mutations:
            with self.subTest(mutated=mutated):
                with self.assertRaises(ValueError):
                    controller.authorize_envelope(self.authorization, self.intent, mutated, now=1_000)
        self.assertFalse(controller.is_consumed(self.intent.intent_hash()))

    def test_replay_is_rejected_after_exact_envelope_consumption(self):
        controller = AuthorizationController()
        controller.authorize_envelope(self.authorization, self.intent, self.envelope, now=1_000)
        with self.assertRaises(ValueError):
            controller.authorize_envelope(self.authorization, self.intent, self.envelope, now=1_001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
