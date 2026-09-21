import unittest
from decimal import Decimal

from phantomx.native_valuation import NativeValuationError, build_conservative_native_valuation, observation_from_quote
from phantomx.quote_snapshot import QuoteSnapshot

class NativeValuationTests(unittest.TestCase):
    def quote(self, amount_out, h):
        fields=dict(schema_version=1,chain_id=137,block_number=100,observed_at_unix=1,dex="test",pool_or_router="0x"+"11"*20,token_in="0x"+"aa"*20,token_out="0x"+"bb"*20,amount_in=10**18,amount_out=amount_out,fee_raw=0,gas_estimate=None,quote_hash="")
        from phantomx.hashing import keccak256_hex
        import json
        fields["quote_hash"]=keccak256_hex(json.dumps({k:v for k,v in fields.items() if k!="quote_hash"},sort_keys=True,separators=(",",":")).encode())
        return QuoteSnapshot(**fields)

    def test_exact_quote_gives_native_usd_price(self):
        obs=observation_from_quote(self.quote(500000,"a"),native_token="0x"+"aa"*20,stable_token="0x"+"bb"*20)
        self.assertEqual(obs.price_usd, Decimal("0.5"))

    def test_conservative_price_uses_highest_same_block_observation(self):
        a=observation_from_quote(self.quote(500000,"a"),native_token="0x"+"aa"*20,stable_token="0x"+"bb"*20)
        b=observation_from_quote(self.quote(600000,"b"),native_token="0x"+"aa"*20,stable_token="0x"+"bb"*20)
        result=build_conservative_native_valuation((a,b))
        self.assertEqual(result.conservative_price_usd, Decimal("0.6"))

    def test_mismatched_block_is_rejected(self):
        a=observation_from_quote(self.quote(500000,"a"),native_token="0x"+"aa"*20,stable_token="0x"+"bb"*20)
        with self.assertRaises(NativeValuationError):
            build_conservative_native_valuation((a, type(a)(**{**a.__dict__,"block_number":101})))

if __name__=="__main__":
    unittest.main(verbosity=2)
