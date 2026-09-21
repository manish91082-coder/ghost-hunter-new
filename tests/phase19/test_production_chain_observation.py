import unittest
from phantomx.chain_observer import ChainObservationState
from phantomx.polygon_rpc import RPCProvider
from phantomx.production_chain_observation import ProductionChainObservationError, observe_production_chain_quorum

TX='0x'+'11'*32
SENDER='0x'+'22'*20
BLOCK='0x'+'33'*32


def p(name, present=True, receipt=True, status=1, canonical=BLOCK, pending='0x8'):
    def t(method,*params):
        if method=='eth_chainId': return {'result':'0x89'}
        if method=='eth_blockNumber': return {'result':'0x3e8'}
        if method=='eth_getTransactionCount': return {'result':pending}
        if method=='eth_getTransactionByHash': return {'result':({'hash':TX,'nonce':'0x7'} if present else None)}
        if method=='eth_getTransactionReceipt': return {'result':({'transactionHash':TX,'status':hex(status),'blockHash':BLOCK,'blockNumber':'0x3e7'} if receipt else None)}
        if method=='eth_getBlockByNumber': return {'result':{'hash':canonical}}
        raise AssertionError(method)
    return RPCProvider(name,t)

class T(unittest.TestCase):
    def test_included_quorum(self):
        r=observe_production_chain_quorum([p('a'),p('b')],tx_hash=TX,sender=SENDER,tx_nonce=7,quorum=2)
        self.assertEqual(r.decision.state,ChainObservationState.INCLUDED)
    def test_reverted_quorum(self):
        r=observe_production_chain_quorum([p('a',status=0),p('b',status=0)],tx_hash=TX,sender=SENDER,tx_nonce=7,quorum=2)
        self.assertEqual(r.decision.state,ChainObservationState.REVERTED)
    def test_pending_quorum(self):
        r=observe_production_chain_quorum([p('a',receipt=False),p('b',receipt=False)],tx_hash=TX,sender=SENDER,tx_nonce=7,quorum=2)
        self.assertEqual(r.decision.state,ChainObservationState.PENDING)
    def test_reorg_quorum(self):
        r=observe_production_chain_quorum([p('a',canonical='0x'+'44'*32),p('b',canonical='0x'+'44'*32)],tx_hash=TX,sender=SENDER,tx_nonce=7,quorum=2)
        self.assertEqual(r.decision.state,ChainObservationState.REORGED)
    def test_split_fails(self):
        with self.assertRaises(ProductionChainObservationError):
            observe_production_chain_quorum([p('a'),p('b',status=0)],tx_hash=TX,sender=SENDER,tx_nonce=7,quorum=2)

if __name__=='__main__': unittest.main()
