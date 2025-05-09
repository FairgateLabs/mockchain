import unittest
from mockchain.bitcoin import Bitcoin, Output, Input, Script, Address
from mockchain.blockchain import Wallet
from asyncio import gather, sleep, Future, Event, run
import pytest

def bitcoin_fixture():
        bitcoin = Bitcoin()
        faucet = bitcoin.faucet
        alice = Wallet('alice')
        bob = Wallet('bob')
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

    
    
    async def test_wait_for_utxo(self):
        bitcoin, faucet, alice, bob = bitcoin_fixture()
        
        tx = bitcoin.transfer(bitcoin.faucet, alice, 1000)
        bitcoin.add_transaction(tx)
        bitcoin.mine_block()
        
        utxo = tx.outputs[0].ptr
        tx2 = bitcoin.transfer(alice, bob, 500)
        
        async def wait_for_tx():
            return await bitcoin.wait_for_utxo(utxo, min_height = 0)
        
        async def mine_block():
            for i in range(10):
                bitcoin.mine_block()

            bitcoin.add_transaction(tx2)

            for i in range(10):
                bitcoin.mine_block()

            return True
        
        result = await gather(wait_for_tx(), mine_block())
        tx2b = result[0]
        
        self.assertEqual(tx2b, tx2)

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
