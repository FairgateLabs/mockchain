import unittest
from mockchain.blockchain import User, TransactionStatus
from mockchain.cardano import Cardano, Value, ScriptContext, ScriptPurpose


class TestValue(unittest.TestCase):
    def test_add(self):
        value = Value.ADA(100)
        value2 = Value({"test" : { "Random" : 100}, "" : { "ADA" : 200 } })
        value3 = value + value2
        self.assertEqual(value3.value, {"": { "ADA": 300 }, "test" : {"Random" : 100} })

    def test_sub(self):
        value = Value.ADA(100)
        value2 = Value.ADA(200)
        value3 = value + value2
        self.assertEqual(value3.value, {"": { "ADA": 300 }})

class TestScripts(unittest.TestCase):
    def test_mint(self):
        cardano = Cardano()
        alice = User('alice')
        called = False

        def validation_script(redeemer, context):
            nonlocal called
            called = True
            return True
        
     
        policy = cardano.add_policy(validation_script)

        value = Value.Token(policy, "test", 1000)

        tx = cardano.create_mint_transaction(value, alice)
        tx.sign(alice)
        cardano.add_transaction(tx)
        cardano.mine_block()

        self.assertTrue(called)
        self.assertEqual(cardano.utxo_set[tx.outputs[0].ptr].value, value)
        self.assertEqual(tx.status, TransactionStatus.CONFIRMED)

    def test_refuse(self):
        cardano = Cardano()
        alice = User('alice')
        called = False

        def validation_script(redeemer, context):
            nonlocal called
            called = True
            return False
        
     
        policy = cardano.add_policy(validation_script)

        value = Value.Token(policy, "test", 1000)

        tx = cardano.create_mint_transaction(value, alice)
        tx.sign(alice)
        cardano.add_transaction(tx)
        cardano.mine_block()

        self.assertTrue(called)
        self.assertFalse(tx.outputs[0].ptr in cardano.utxo_set)
        self.assertEqual(tx.status, TransactionStatus.FAILED)

    def test_mint1(self):
        cardano = Cardano()
        alice = User('alice')
        called = 0

        def validation_script(redeemer, context : ScriptContext):
            nonlocal called
            called += 1

            policy = context.policy
            
            tx = context.txinfo
            mint = tx.mint[(policy, token)]
            

            if redeemer != "minting" and redeemer != "burning":
                return False

            if mint != 1 and redeemer == "minting":
                return False
            
            if mint != -1 and redeemer == "burning":
                return False
            
            return True
        
        policy = cardano.add_policy(validation_script)
        token = "NFT"
        
        tx1 = cardano.create_mint_transaction(Value.Token(policy, token, 1), alice)
        tx1.set_redeemer(policy, "minting")
        tx1.sign(alice)
        cardano.add_transaction(tx1)

        tx2 = cardano.create_transaction([tx1.outputs[0].ptr], [], mint=Value.Token(policy, token, -1))
        tx2.set_redeemer(policy,"burning")
        tx2.sign(alice)
        cardano.add_transaction(tx2)

        cardano.mine_block()
        self.assertEqual(called, 2)
        self.assertEqual(tx1.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx2.status, TransactionStatus.CONFIRMED)

