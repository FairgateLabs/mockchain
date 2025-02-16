import unittest
from mockchain.bitcoin import Bitcoin, Output, Input, Script
from mockchain.blockchain import User


class TestBitcoin(unittest.TestCase):
    def test_transfer(self):
        blockchain = Bitcoin()
        faucet = blockchain.faucet
        alice = User('alice')

        tx = blockchain.transfer(faucet, alice, 1000)
        blockchain.add_transaction(tx)
        blockchain.mine_block()

        utxos = blockchain.UTXOs_for_address(alice)
        self.assertEqual(len(utxos), 1)

        self.assertEqual(blockchain.utxo_set[utxos[0]].amount, 1000)

        self.assertEqual(tx.sequence, 0)
        
class TestOrdinals(unittest.TestCase):
    def test_presupply(self):
        blockchain = Bitcoin(supply=100)
        genesis = blockchain.utxo_set["genesis:0"]
        self.assertEqual(genesis.amount, 100)
        self.assertEqual(genesis.ordinals, [(0, 100)])

    def test_reward(self):
        blockchain = Bitcoin(supply=100)
        alice=User("alice")
        blockchain.mine_block(miner=alice)
        outputs = blockchain.UTXOs_for_address(alice)
        self.assertEqual(len(outputs), 1)
        self.assertEqual(blockchain.utxo_set[outputs[0]].amount, 50)
        self.assertEqual(blockchain.utxo_set[outputs[0]].ordinals, [(100, 150)])

    def test_split(self):
        blockchain = Bitcoin(supply=100)
        alice=User("alice")
        bob=User('bob')

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