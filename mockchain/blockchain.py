from mockchain.crypto import Secret, Key
from typing import Union, List, Callable, Optional
from mockchain.crypto import Key, Public
from enum import Enum
from asyncio import Future

class User:
    def __init__(self, name):
        self.name = name
        self.key = Key(name)
        self.public = self.key.public

    def get_public(self):
        return self.public
    
    def sign(self, msg):
        return self.key.sign(msg)
    

Address = Union[str, User, Public]

def get_public(addr : Address ) -> Address:
    if type(addr) is str:
        return Key.publics[addr]
    elif type(addr) is User:
        return addr.get_public()
    else:
        return addr


class TransactionStatus(Enum):
    CREATED = "created"
    SIGNED = "signed"
    PARTIALLY_SIGNED = "partially_signed"
    CONFIRMED = "confirmed"
    FAILED = "failed"

    def __str__(self):
        return self.value

class Transaction:
    pass

class Blockchain:
    def __init__(self):
        self.subscribers = []


    def add_transaction(self, transaction : Transaction):
        pass

    def transfer(self, source : User, destination : User, amount : int) -> Transaction:
        pass

    def sweep(self, user : User) -> Transaction:
        pass

    def create_transaction(self) -> Transaction:
        pass

    def mine_transaction(self, transaction : Transaction, check_inputs : bool = True) -> bool:
        pass

    def mine_block(self, cnt=1, miner : Address = None):
        pass

    def subscribe(self, future : Future):
        self.subscribers.append(future)

    def notify(self, block):
        subscribers = self.subscribers
        self.subscribers = []

        for future, min_height in subscribers:
            if min_height < len(self.blocks): 
                future.set_result(self.blocks[min_height])
            else:
                self.subscribe((future, min_height))

    async def wait_for_transaction(self, tx, min_height : Optional[int] = None,  max_blocks : Optional[int] = None):
        if tx.status == TransactionStatus.CONFIRMED:
            return True
            
        if tx.status == TransactionStatus.FAILED:
            return False
            
        async for block in self.block_iterator(min_height=min_height, max_blocks=max_blocks):
            if tx.status == TransactionStatus.CONFIRMED:
                return True
            
            if tx.status == TransactionStatus.FAILED:
                return False
            
        return False

    async def wait_for_transaction_hash(self, hash : str | set[str], min_height : Optional[int] = None, max_blocks : Optional[int]=None):
        if type(hash) is str:
            hash = {hash}

        async for tx in self.transaction_iterator(min_height=min_height, max_blocks=max_blocks):
            if tx.hash in hash:
                return tx

    async def wait_for_block(self, min_height : Optional[int] = None):
        if min_height is None:
            min_height = len(self.blocks)

        if len(self.blocks) > min_height:
            return self.blocks[min_height]
        
        future = Future()
        self.subscribe((future, min_height))
        return await future
    
    async def block_iterator(self, min_height : Optional[int] = None, max_blocks : Optional[int] = None):
        if min_height is None:
            min_height = len(self.blocks)

        while True:
            block = await self.wait_for_block(min_height)
            yield block

            min_height += 1
            if max_blocks is not None:
                max_blocks -= 1
                if max_blocks == 0:
                    break

    async def transaction_iterator(self, min_height : Optional[int] = None, max_blocks : Optional[int] = None):
        async for block in self.block_iterator(min_height=min_height, max_blocks=max_blocks):
            for tx in block:
                yield tx
