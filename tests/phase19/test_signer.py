import unittest
from dataclasses import replace

from phantomx.execution import Authorization, ExecutionIntent, TransactionEnvelope
from phantomx.governor import GovernorDecision
from phantomx.hashing import keccak256_hex
from phantomx.signer import EthereumEip1559Signer, SignerError, recover_eip1559_sender, sign_governed_transaction


TOKEN = "0x" + "aa" * 20
EXECUTOR = "0x" + "bb" * 20
ROUTE = "0x" + "11" * 32
ECONOMIC = "0x" + "22" * 32
SIMULATION = "0x" + "33" * 32
CALldata = b"phase19-calldata"
PRIVATE_KEY = "0x" + "01" * 32


class SignerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000
        self.signer = EthereumEip1559Signer(PRIVATE_KEY)
        self.sender = self.signer.address
        self.intent = ExecutionIntent(
            chain_id=137, executor=EXECUTOR, sender=self.sender, loan_asset=TOKEN,
            loan_amount=100, route_hash=ROUTE,
            calldata_hash=keccak256_hex(CALldata), economic_proof_hash=ECONOMIC,
            simulation_proof_hash=SIMULATION, nonce=7, deadline=self.now + 60,
        )
        self.envelope = TransactionEnvelope(
            chain_id=137, sender=self.sender, executor=EXECUTOR, nonce=7,
            calldata=CALldata, gas_limit=300_000, max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
        )
        self.authorization = Authorization(
            intent_hash=self.intent.intent_hash(), calldata_hash=self.intent.calldata_hash,
            economic_proof_hash=ECONOMIC, simulation_proof_hash=SIMULATION,
            chain_id=137, executor=EXECUTOR, sender=self.sender, nonce=7,
            deadline=self.intent.deadline, gas_limit=300_000,
            max_fee_per_gas=100, max_priority_fee_per_gas=30,
        )
        self.governor = GovernorDecision(
            approved=True, reason="all governor policy gates passed", chain_id=137,
            block_number=5000, intent_hash=self.intent.intent_hash(), route_hash=ROUTE,
            economic_proof_hash=ECONOMIC, simulation_proof_hash=SIMULATION,
            calldata_hash=self.envelope.calldata_hash, ai_rank="0.9",
        )

    def sign(self, **overrides):
        values = {
            "signer": self.signer, "governor": self.governor, "intent": self.intent,
            "authorization": self.authorization, "envelope": self.envelope, "now": self.now,
        }
        values.update(overrides)
        return sign_governed_transaction(**values)

    def test_exact_governed_eip1559_transaction_signs_and_recovers(self):
        result = self.sign()
        self.assertEqual(result.transaction_hash, keccak256_hex(result.raw_transaction))
        self.assertEqual(result.intent_hash, self.intent.intent_hash())
        self.assertEqual(result.raw_transaction[:1], b"\x02")
        self.assertEqual(recover_eip1559_sender(result.raw_transaction), self.sender)

    def test_signer_private_key_identity_is_explicit(self):
        self.assertEqual(len(self.signer.address), 42)
        self.assertEqual(self.signer.address, recover_eip1559_sender(self.signer.sign(self.envelope)))

    def test_wrong_signer_identity_is_blocked_before_signing(self):
        wrong = EthereumEip1559Signer("0x" + "02" * 32)
        with self.assertRaisesRegex(SignerError, "signer identity"):
            self.sign(signer=wrong)

    def test_recovered_sender_mismatch_is_blocked(self):
        foreign = EthereumEip1559Signer("0x" + "02" * 32)
        intent = replace(self.intent, sender=foreign.address)
        authorization = replace(
            self.authorization,
            intent_hash=intent.intent_hash(),
            sender=foreign.address,
        )
        governor = GovernorDecision(
            approved=True,
            reason="all governor policy gates passed",
            chain_id=137,
            block_number=5000,
            intent_hash=intent.intent_hash(),
            route_hash=ROUTE,
            economic_proof_hash=ECONOMIC,
            simulation_proof_hash=SIMULATION,
            calldata_hash=self.envelope.calldata_hash,
            ai_rank="0.9",
        )
        with self.assertRaisesRegex(SignerError, "signer identity"):
            self.sign(intent=intent, authorization=authorization, governor=governor)

    def test_governor_block_prevents_signer_call(self):
        blocked = GovernorDecision(
            approved=False,
            reason="locked",
            chain_id=self.governor.chain_id,
            block_number=self.governor.block_number,
            intent_hash=self.governor.intent_hash,
            route_hash=self.governor.route_hash,
            economic_proof_hash=self.governor.economic_proof_hash,
            simulation_proof_hash=self.governor.simulation_proof_hash,
            calldata_hash=self.governor.calldata_hash,
            ai_rank=self.governor.ai_rank,
        )
        with self.assertRaises(SignerError):
            self.sign(governor=blocked)

    def test_mutations_are_blocked_before_signing(self):
        mutations = [
            {"intent": replace(self.intent, route_hash="0x" + "44" * 32)},
            {"intent": replace(self.intent, economic_proof_hash="0x" + "55" * 32)},
            {"intent": replace(self.intent, simulation_proof_hash="0x" + "66" * 32)},
            {"envelope": replace(self.envelope, calldata=b"mutated")},
            {"envelope": replace(self.envelope, nonce=8)},
        ]
        for mutation in mutations:
            with self.assertRaises(SignerError):
                self.sign(**mutation)

    def test_authorization_mutation_is_blocked(self):
        mutated = replace(self.authorization, gas_limit=300_001)
        with self.assertRaises(SignerError):
            self.sign(authorization=mutated)

    def test_expired_deadline_is_blocked(self):
        with self.assertRaises(SignerError):
            self.sign(now=self.intent.deadline + 1)

    def test_recovery_rejects_non_type2_bytes(self):
        with self.assertRaises(SignerError):
            recover_eip1559_sender(b"\x01garbage")


if __name__ == "__main__":
    unittest.main(verbosity=2)
