import unittest
from mockchain.bitcoin import Bitcoin, Output, Input, Script
from mockchain.blockchain import Wallet, TransactionStatus


class TestBitcoin(unittest.TestCase):
    def test_transfer(self):
        blockchain = Bitcoin()
        faucet = blockchain.faucet
        alice = Wallet('alice')

        tx = blockchain.transfer(faucet, alice, 1000)
        blockchain.add_transaction(tx)
        blockchain.mine_block()

        utxos = blockchain.UTXOs_for_address(alice)
        self.assertEqual(len(utxos), 1)

        self.assertEqual(blockchain.utxo_set[utxos[0]].amount, 1000)

        self.assertEqual(tx.sequence, 0)

    def test_double_spend(self):
        blockchain = Bitcoin()
        faucet = blockchain.faucet
        alice = Wallet('alice')
        bob = Wallet('bob')

        tx = blockchain.transfer(faucet, alice, 1)
        blockchain.add_transaction(tx)
        blockchain.mine_block()

        o2 = Output(1, Script.p2pubkey(bob))
        tx2 = blockchain.create_transaction([tx.outputs[0].ptr], [o2])
        tx2.sign(alice)
        blockchain.add_transaction(tx2)
        blockchain.mine_block()

        tx3 = blockchain.create_transaction([tx.outputs[0].ptr], [o2])
        tx3.sign(alice)
        blockchain.add_transaction(tx3)
        blockchain.mine_block()

        self.assertEqual(tx.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx2.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx3.status, TransactionStatus.FAILED)


        
        
class TestOrdinals(unittest.TestCase):
    def test_presupply(self):
        blockchain = Bitcoin(supply=100)
        genesis = blockchain.utxo_set["genesis:0"]
        self.assertEqual(genesis.amount, 100)
        self.assertEqual(genesis.ordinals, [(0, 100)])

    def test_reward(self):
        blockchain = Bitcoin(supply=100)
        alice=Wallet("alice")
        blockchain.mine_block(miner=alice)
        outputs = blockchain.UTXOs_for_address(alice)
        self.assertEqual(len(outputs), 1)
        self.assertEqual(blockchain.utxo_set[outputs[0]].amount, 50)
        self.assertEqual(blockchain.utxo_set[outputs[0]].ordinals, [(100, 150)])

    def test_split(self):
        blockchain = Bitcoin(supply=100)
        alice=Wallet("alice")
        bob=Wallet('bob')

        blockchain.mine_block(miner=alice)
        inputs = blockchain.UTXOs_for_address(alice)
        outputs = [ Output(10, Script.p2pubkey(bob)), Output(40, Script.p2pubkey(bob)) ]

        tx = blockchain.create_transaction(inputs, outputs)
        tx.sign(alice)
        blockchain.add_transaction(tx)
        blockchain.mine_block()
        
        output0 = outputs[0]
        output1 = outputs[1]

        self.assertEqual(output0.amount, 10)
        self.assertEqual(output0.ordinals, [(100, 110)])
        self.assertEqual(output1.amount, 40)
        self.assertEqual(output1.ordinals, [(110, 150)])

        output3 = Output(50, Script.p2pubkey(bob))
        tx2 = blockchain.create_transaction([output1.ptr, output0.ptr], [output3])
        tx2.sign(bob)
        blockchain.add_transaction(tx2)
        blockchain.mine_block()

        self.assertEqual(output3.amount, 50)
        self.assertEqual(output3.ordinals, [(110, 150), (100, 110)])
        
if __name__ == '__main__':
    unittest.main()