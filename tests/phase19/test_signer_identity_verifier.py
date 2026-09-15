import unittest

from phantomx.signer import EthereumEip1559Signer, SignerError
from phantomx.signer_identity_verifier import verify_signer_identity_proof

PRIVATE_KEY = "0x" + "01" * 32
WRONG_PRIVATE_KEY = "0x" + "02" * 32


class SignerIdentityVerifierTests(unittest.TestCase):
    def setUp(self):
        self.signer = EthereumEip1559Signer(PRIVATE_KEY)
        self.challenge = b"V" * 32

    def test_verifies_external_signature_without_signer_object(self):
        signature = self.signer.sign_challenge(self.challenge)
        evidence = verify_signer_identity_proof(
            expected_address=self.signer.address,
            challenge=self.challenge,
            signature=signature,
        )
        self.assertEqual(evidence.challenge_hash, "0x" + __import__("phantomx.hashing", fromlist=["keccak256_hex"]).keccak256_hex(self.challenge)[2:])
        self.assertEqual(evidence.expected_address, self.signer.address)
        self.assertEqual(evidence.recovered_address, self.signer.address)
        self.assertEqual(len(evidence.signature), 65)

    def test_wrong_expected_address_is_blocked(self):
        signature = self.signer.sign_challenge(self.challenge)
        wrong_address = EthereumEip1559Signer(WRONG_PRIVATE_KEY).address
        with self.assertRaisesRegex(SignerError, "challenge identity"):
            verify_signer_identity_proof(
                expected_address=wrong_address,
                challenge=self.challenge,
                signature=signature,
            )

    def test_mutated_challenge_is_blocked(self):
        signature = self.signer.sign_challenge(self.challenge)
        with self.assertRaisesRegex(SignerError, "challenge identity"):
            verify_signer_identity_proof(
                expected_address=self.signer.address,
                challenge=b"W" * 32,
                signature=signature,
            )

    def test_invalid_signature_length_is_blocked(self):
        with self.assertRaisesRegex(SignerError, "exactly 65"):
            verify_signer_identity_proof(
                expected_address=self.signer.address,
                challenge=self.challenge,
                signature=b"bad",
            )

    def test_invalid_challenge_length_is_blocked(self):
        signature = self.signer.sign_challenge(self.challenge)
        with self.assertRaisesRegex(SignerError, "exactly 32"):
            verify_signer_identity_proof(
                expected_address=self.signer.address,
                challenge=b"short",
                signature=signature,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
