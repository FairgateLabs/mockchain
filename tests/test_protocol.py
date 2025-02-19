from mockchain.protocol import Protocol
from mockchain.bitcoin import Bitcoin, Output, Script
from mockchain.blockchain import Wallet, Address
import unittest




class TestParameters(unittest.TestCase):
    def test_create(self):
        protocol = Protocol()
        v1 = protocol.var()
        v2 = protocol.var()
        v3 = protocol.var("hello")

        self.assertEqual(v1, "$var0")
        self.assertEqual(v2, "$var1")
        self.assertEqual(v3, "$hello")

    def test_bitcoin_transaction(self):
        protocol = Protocol()
        utxo = protocol.var("utxo")
        tx0 = protocol.var("tx0")

        alice = protocol.var("alice")
        amount = protocol.var("amount")

        inputs = [ utxo, tx0+":0"]

        bitcoin = Bitcoin()


        vutxo = "genesis:0"
        vtx0 = "tx1234"
        valice = "alice1234"
        vamount = 2345

        protocol.set(utxo, vutxo)
        protocol.set(tx0, vtx0)
        protocol.set(alice, valice)
        protocol.set(amount, vamount)

        tx1 = protocol.create_transaction(inputs, [Output(amount, Script.p2pubkey(alice))])
        tx1x = tx1.apply(protocol)

        i0 = tx1x.inputs[0]
        i1 = tx1x.inputs[1]
        o1 = tx1x.outputs[0]

        self.assertTrue(o1.is_p2pubkey(valice))
        self.assertEqual(o1.amount, vamount)
        self.assertEqual(i0.ptr, vutxo)
        self.assertEqual(i1.ptr, vtx0+":0")

        

    def test_apply(self):
        protocol = Protocol()
        
        utx0 = protocol.var("utx0")
        alice = protocol.user("alice")

        t0 = protocol.create_transaction([utx0], Output(100, Script.p2pubkey(alice))).hash
        t1 = protocol.create_transaction(t0+":0", [Output(100, Script.p2pubkey(alice))]).hash
        t2 = protocol.create_transaction([t1+":0"], [Output(100, Script.p2pubkey(alice))]).hash
        t3 = protocol.create_transaction([t2+":0"], [Output(100, Script.p2pubkey(alice))]).hash

        data = [{utx0:"genesis:0", alice:"alice0"}, {utx0:"genesis:1", alice:"bob"} ]

        txs = [ protocol.apply(data[0]), protocol.apply(data[1])]

        for i in range(len(data)):
            tx = txs[i]
            info = data[i]
            self.assertEqual(tx[0].inputs[0].ptr, info[utx0])
            self.assertEqual(tx[0].outputs[0].amount, 100)
            self.assertTrue(tx[0].outputs[0].is_p2pubkey(info[alice]))
            self.assertEqual(tx[1].inputs[0].ptr, tx[0].outputs[0].hash)
            self.assertEqual(tx[1].outputs[0].amount, 100)
            self.assertTrue(tx[1].outputs[0].is_p2pubkey(info[alice]))
            self.assertEqual(tx[2].inputs[0].ptr, tx[1].outputs[0].hash)
            self.assertEqual(tx[2].outputs[0].amount, 100)
            self.assertTrue(tx[2].outputs[0].is_p2pubkey(info[alice]))
            self.assertEqual(tx[3].inputs[0].ptr, tx[2].outputs[0].hash)
            self.assertEqual(tx[3].outputs[0].amount, 100)
            self.assertTrue(tx[3].outputs[0].is_p2pubkey(info[alice]))

