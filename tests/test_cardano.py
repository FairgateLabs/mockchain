import unittest
from mockchain.blockchain import Wallet, TransactionStatus
from mockchain.cardano import Cardano, Value, ScriptContext, ScriptPurpose, Output
from mockchain.program import Program

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

class TestTransactions(unittest.TestCase):
    def test_transfer(self):
        cardano = Cardano()
        faucet = cardano.faucet
        alice = Wallet('alice')
        bob = Wallet('bob')

        tx = cardano.transfer(faucet, alice, 100)
        cardano.add_transaction(tx)
        cardano.mine_block()
        self.assertEqual(tx.status, TransactionStatus.CONFIRMED)

        o2 = Output(bob, Value.ADA(100))
        tx2 = cardano.create_transaction([tx.outputs[0].ptr], [o2])
        tx2.sign(bob)
        cardano.add_transaction(tx2)
        cardano.mine_block()
        self.assertEqual(tx2.status, TransactionStatus.FAILED)


class TestScripts(unittest.TestCase):
    def test_pay2script(self):
        cardano = Cardano()
        alice = Wallet('alice')
        bob = Wallet('bob')
        called = False

        def validation_script(redeemer, context):
            return True
        
        tx1 = cardano.transfer(cardano.faucet, alice, 100)

        program_address = Program.address(validation_script)

        o1 = Output(program_address, 100)
        tx2 = cardano.create_transaction([tx1.outputs[0].ptr], [o1])
        tx2.sign(alice)

        o2 = Output(bob, 100)
        tx3 = cardano.create_transaction([tx2.outputs[0].ptr], [o2])

        cardano.add_transaction(tx1)
        cardano.add_transaction(tx2)
        cardano.add_transaction(tx3)

        program_address.program.cnt = 0
        cardano.mine_block()
   
        self.assertEqual(program_address.program.cnt, 1)
        
        self.assertEqual(tx1.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx2.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx3.status, TransactionStatus.CONFIRMED)


    def test_pay2script_fail(self):
        cardano = Cardano()
        alice = Wallet('alice')
        bob = Wallet('bob')
        called = False

        def validation_script(redeemer, context):
            return False
        
        program_address = Program.address(validation_script)

        tx1 = cardano.transfer(cardano.faucet, alice, 100)

        o1 = Output(program_address, 100)
        tx2 = cardano.create_transaction([tx1.outputs[0].ptr], [o1])
        tx2.sign(alice)

        o2 = Output(bob, 100)
        tx3 = cardano.create_transaction([tx2.outputs[0].ptr], [o2])

        cardano.add_transaction(tx1)
        cardano.add_transaction(tx2)
        cardano.add_transaction(tx3)

        program_address.program.cnt = 0
        cardano.mine_block()

        self.assertEqual(program_address.program.cnt, 1)
        
        self.assertEqual(tx1.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx2.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx3.status, TransactionStatus.FAILED)

    def test_mint(self):
        cardano = Cardano()
        alice = Wallet('alice')
        
        def validation_script(redeemer, context):
            return True
        
     
        policy = Program.address(validation_script)
        value = Value.Token(policy, "test", 1000)

        tx = cardano.create_mint_transaction(value, alice)
        tx.sign(alice)
        cardano.add_transaction(tx)

        policy.program.cnt = 0
        cardano.mine_block()

        self.assertEqual(policy.program.cnt, 1)
        self.assertEqual(cardano.utxo_set[tx.outputs[0].ptr].value, value)
        self.assertEqual(tx.status, TransactionStatus.CONFIRMED)

    def test_refuse(self):
        cardano = Cardano()
        alice = Wallet('alice')
        called = False

        def validation_script(redeemer, context):
            return False
           
        policy = Program.address(validation_script)

        value = Value.Token(policy, "test", 1000)

        tx = cardano.create_mint_transaction(value, alice)
        tx.sign(alice)
        cardano.add_transaction(tx)
        policy.program.cnt = 0
        cardano.mine_block()

        self.assertEqual(policy.program.cnt, 1)
        self.assertFalse(tx.outputs[0].ptr in cardano.utxo_set)
        self.assertEqual(tx.status, TransactionStatus.FAILED)

    def test_mint1(self):
        cardano = Cardano()
        alice = Wallet('alice')
        called = 0

        def validation_script(redeemer, context):
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
        
        token = "NFT"
        policy = Program.address(validation_script, token=token)
        
        tx1 = cardano.create_mint_transaction(Value.Token(policy, token, 1), alice)
        tx1.set_redeemer(policy, "minting")
        tx1.sign(alice)
        cardano.add_transaction(tx1)

        tx2 = cardano.create_transaction([tx1.outputs[0].ptr], [], mint=Value.Token(policy, token, -1))
        tx2.set_redeemer(policy,"burning")
        tx2.sign(alice)
        cardano.add_transaction(tx2)
        policy.program.cnt = 0
        cardano.mine_block()
        self.assertEqual(policy.program.cnt, 2)
        self.assertEqual(tx1.status, TransactionStatus.CONFIRMED)
        self.assertEqual(tx2.status, TransactionStatus.CONFIRMED)