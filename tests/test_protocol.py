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
        
        utxo0 = protocol.var("utxo0")
        alice = protocol.user("alice")

        t0 = protocol.create_transaction([utxo0], Output(100, Script.p2pubkey(alice))).hash
        t1 = protocol.create_transaction(t0+":0", [Output(100, Script.p2pubkey(alice))]).hash
        t2 = protocol.create_transaction([t1+":0"], [Output(100, Script.p2pubkey(alice))]).hash
        t3 = protocol.create_transaction([t2+":0"], [Output(100, Script.p2pubkey(alice))]).hash

        data = [{utxo0:"genesis:0", alice:"alice0"}, {utxo0:"genesis:1", alice:"bob"} ]

        txs = [ protocol.apply(data[0]), protocol.apply(data[1])]

        for i in range(len(data)):
            tx = [ t[0] for t in txs[i]]
            info = data[i]
            self.assertEqual(tx[0].inputs[0].ptr, info[utxo0])
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

    def test_multiplicity(self):
        protocol = Protocol()
        utxo0 = protocol.var("utxo0")
        utxo1 = protocol.var("utxo1")
        alice = protocol.user("alice")
        amount = protocol.var("amount")

        t0 = protocol.create_transaction([utxo0], Output(amount, Script.p2pubkey(alice))).hash
        t1 = protocol.create_transaction([utxo1], [Output(amount, Script.p2pubkey(alice))]).hash
        t2 = protocol.create_transaction(["$tx0:0|$tx1:0"], [Output(amount, Script.p2pubkey(alice))]).hash
        t3 = protocol.create_transaction(["$tx2:0"], [Output(amount, Script.p2pubkey(alice))]).hash
        t4 = protocol.create_transaction(["$tx0:0|$tx1:0|$tx2:0|$tx3:0"], [Output(amount, Script.p2pubkey(alice))]).hash
        data = { utxo0:"genesis:0", utxo1:"genesis:1", alice:"alice0", amount:100}
        txs = protocol.apply(data)

        self.assertEqual(len(txs), 5)
        self.assertEqual([len(tx) for tx in txs], [1,1,2,2,6])    

        tx0 = txs[0][0]
        tx1 = txs[1][0]
        tx20 = txs[2][0]
        tx21 = txs[2][1]
        tx30 = txs[3][0]
        tx31 = txs[3][1]

        self.assertEqual(tx0.inputs[0].ptr, "genesis:0")
        self.assertEqual(tx1.inputs[0].ptr, "genesis:1")
        self.assertEqual(tx20.inputs[0].ptr, tx0.outputs[0].hash)
        self.assertEqual(tx21.inputs[0].ptr, tx1.outputs[0].hash)
        self.assertEqual(tx30.inputs[0].ptr, tx20.outputs[0].hash)
        self.assertEqual(tx31.inputs[0].ptr, tx21.outputs[0].hash)