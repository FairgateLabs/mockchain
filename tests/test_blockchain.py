import unittest
from mockchain.bitcoin import Bitcoin, Output, Input, Script, Address
from mockchain.blockchain import User, Parameters
from asyncio import gather, sleep, Future, Event, run
import pytest

def bitcoin_fixture():
        bitcoin = Bitcoin()
        faucet = bitcoin.faucet
        alice = User('alice')
        bob = User('bob')
        return bitcoin, faucet, alice, bob


class TestBlockchain(unittest.IsolatedAsyncioTestCase):
    async def test_wait(self):
        bitcoin, faucet, alice, bob = bitcoin_fixture()

        async def wait_for_block():
            num = 0
            block1 = await bitcoin.wait_for_block(num)
            block2 = await bitcoin.wait_for_block(num+1)
            
            return True
        
        async def mine_blocks():
            bitcoin.mine_block()
            bitcoin.mine_block()
            return True

        
        result = await gather(wait_for_block(), mine_blocks())
        self.assertTrue(result)

    async def test_wait_for_transaction(self):
        bitcoin, faucet, alice, bob = bitcoin_fixture()
        
        tx = bitcoin.transfer(bitcoin.faucet, alice, 1000)
        bitcoin.add_transaction(tx)
        bitcoin.mine_block()
        
        tx2 = bitcoin.transfer(alice, bob, 500)
        
        async def wait_for_tx():
            return await bitcoin.wait_for_transaction(tx2, min_height = 0)
        
        async def mine_block():
            for i in range(10):
                bitcoin.mine_block()

            bitcoin.add_transaction(tx2)

            for i in range(10):
                bitcoin.mine_block()

            return True
        
        result = await gather(wait_for_tx(), mine_block())
        self.assertTrue(result)

    async def test_wait_for_transaction_hash_max_blocks(self):
        bitcoin, faucet, alice, bob = bitcoin_fixture()
        
        tx = bitcoin.transfer(bitcoin.faucet, alice, 1000)
        bitcoin.add_transaction(tx)
        bitcoin.mine_block()
        
        tx2 = bitcoin.transfer(alice, bob, 500)
        
        async def wait_for_tx():
            return await bitcoin.wait_for_transaction_hash(tx2.hash, min_height = 0, max_blocks = 8)
        
        async def mine_block():
            for i in range(10):
                bitcoin.mine_block()
                
            bitcoin.add_transaction(tx2)

            for i in range(10):
                bitcoin.mine_block()

            return True
        
        result = await gather(wait_for_tx(), mine_block())
        self.assertFalse(result[0])

class TestParameters(unittest.TestCase):
    def test_create(self):
        param = Parameters()
        v1 = param.var()
        v2 = param.var()
        v3 = param.var("hello")

        self.assertEqual(v1, "$$var0")
        self.assertEqual(v2, "$$var1")
        self.assertEqual(v3, "$$hello")

        param[v1] = "hello"
        param[v2] = "world"
        param[v3] = 18

        self.assertEqual(param[v1], "hello")
        self.assertEqual(param[v2], "world")
        self.assertEqual(param[v3], 18)
        self.assertEqual(param.apply("$$var0"), "hello")
        self.assertEqual(param.apply("$$var1"), "world")
        self.assertEqual(param.apply("hola mundo"), "hola mundo")
      
    def test_bitcoin_transaction(self):
        bitcoin = Bitcoin()
        faucet = bitcoin.faucet
        alice = User('alice')
        param = Parameters()
        v1 = param.var()
        v2 = param.var()

        inputs = bitcoin.UTXOs_for_address(faucet)
        tx1 = bitcoin.create_transaction(inputs, [Output(v2, Script.p2pubkey(v1))])

        param[v1] = Address.get_str(alice)
        param[v2] = 1000

        tx1x = param.apply(tx1)
        self.assertTrue(tx1x.outputs[0].is_p2pubkey(alice))
        self.assertEqual(tx1x.outputs[0].amount, 1000)

