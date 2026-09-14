import unittest
from dataclasses import replace

from phantomx.execution import Authorization, ExecutionIntent, TransactionEnvelope
from phantomx.governor import GovernorDecision
from phantomx.hashing import keccak256_hex
from phantomx.private_submit import PrivateSubmitError, submit_governed_transaction
from phantomx.signer import SignedTransaction


TOKEN = "0x" + "aa" * 20
EXECUTOR = "0x" + "bb" * 20
SENDER = "0x" + "cc" * 20
ROUTE = "0x" + "11" * 32
ECONOMIC = "0x" + "22" * 32
SIMULATION = "0x" + "33" * 32
CALldata = b"phase19-calldata"
RAW = b"signed:" + CALldata


class FakeRelay:
    name = "test-private-relay"
    is_private = True

    def __init__(self, result=None, error=None):
        self.calls = 0
        self.payloads = []
        self.result = result or keccak256_hex(RAW)
        self.error = error

    def submit_raw_transaction(self, raw_transaction):
        self.calls += 1
        self.payloads.append(raw_transaction)
        if self.error:
            raise self.error
        return self.result


class PublicRelay:
    name = "public-rpc"
    is_private = False

    def __init__(self):
        self.calls = 0

    def submit_raw_transaction(self, raw_transaction):
        self.calls += 1
        return keccak256_hex(raw_transaction)


class PrivateSubmitBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000
        self.intent = ExecutionIntent(
            chain_id=137, executor=EXECUTOR, sender=SENDER, loan_asset=TOKEN,
            loan_amount=100, route_hash=ROUTE,
            calldata_hash=keccak256_hex(CALldata), economic_proof_hash=ECONOMIC,
            simulation_proof_hash=SIMULATION, nonce=7, deadline=self.now + 60,
        )
        self.envelope = TransactionEnvelope(
            chain_id=137, sender=SENDER, executor=EXECUTOR, nonce=7,
            calldata=CALldata, gas_limit=300_000, max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
        )
        self.authorization = Authorization(
            intent_hash=self.intent.intent_hash(), calldata_hash=self.intent.calldata_hash,
            economic_proof_hash=ECONOMIC, simulation_proof_hash=SIMULATION,
            chain_id=137, executor=EXECUTOR, sender=SENDER, nonce=7,
            deadline=self.intent.deadline, gas_limit=300_000,
            max_fee_per_gas=100, max_priority_fee_per_gas=30,
        )
        self.governor = GovernorDecision(
            approved=True, reason="all governor policy gates passed", chain_id=137,
            block_number=5000, intent_hash=self.intent.intent_hash(), route_hash=ROUTE,
            economic_proof_hash=ECONOMIC, simulation_proof_hash=SIMULATION,
            calldata_hash=self.envelope.calldata_hash, ai_rank="0.9",
        )
        self.signed = SignedTransaction(
            intent_hash=self.intent.intent_hash(), governor_decision_hash=self.governor.decision_hash,
            transaction_hash=keccak256_hex(RAW), raw_transaction=RAW,
        )

    def submit(self, relay, **overrides):
        values = {
            "relay": relay, "signed_transaction": self.signed,
            "governor": self.governor, "intent": self.intent,
            "authorization": self.authorization, "envelope": self.envelope, "now": self.now,
        }
        values.update(overrides)
        return submit_governed_transaction(**values)

    def test_exact_governed_private_submission(self):
        relay = FakeRelay()
        result = self.submit(relay)
        self.assertEqual(relay.calls, 1)
        self.assertEqual(relay.payloads, [RAW])
        self.assertEqual(result.transaction_hash, self.signed.transaction_hash)
        self.assertTrue(result.relay_private)

    def test_public_relay_is_rejected_before_network_io(self):
        relay = PublicRelay()
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay)
        self.assertEqual(relay.calls, 0)

    def test_relay_failure_is_not_retried_through_public_fallback(self):
        relay = FakeRelay(error=RuntimeError("relay unavailable"))
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay)
        self.assertEqual(relay.calls, 1)

    def test_returned_hash_must_match_signed_artifact(self):
        relay = FakeRelay(result="0x" + "99" * 32)
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay)
        self.assertEqual(relay.calls, 1)

    def test_governor_block_prevents_submission(self):
        relay = FakeRelay()
        blocked = GovernorDecision(
            approved=False, reason="locked", chain_id=self.governor.chain_id,
            block_number=self.governor.block_number, intent_hash=self.governor.intent_hash,
            route_hash=self.governor.route_hash, economic_proof_hash=self.governor.economic_proof_hash,
            simulation_proof_hash=self.governor.simulation_proof_hash,
            calldata_hash=self.governor.calldata_hash, ai_rank=self.governor.ai_rank,
        )
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay, governor=blocked)
        self.assertEqual(relay.calls, 0)

    def test_signed_intent_mutation_is_rejected(self):
        relay = FakeRelay()
        mutated = replace(self.signed, intent_hash="0x" + "44" * 32)
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay, signed_transaction=mutated)
        self.assertEqual(relay.calls, 0)

    def test_signed_governor_mutation_is_rejected(self):
        relay = FakeRelay()
        mutated = replace(self.signed, governor_decision_hash="0x" + "55" * 32)
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay, signed_transaction=mutated)
        self.assertEqual(relay.calls, 0)

    def test_calldata_mutation_is_rejected(self):
        relay = FakeRelay()
        mutated = replace(self.envelope, calldata=b"mutated")
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay, envelope=mutated)
        self.assertEqual(relay.calls, 0)

    def test_expired_deadline_is_rejected(self):
        relay = FakeRelay()
        with self.assertRaises(PrivateSubmitError):
            self.submit(relay, now=self.intent.deadline + 1)
        self.assertEqual(relay.calls, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
