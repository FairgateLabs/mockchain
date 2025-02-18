from typing import Callable, Optional
from mockchain.crypto import Key, Public, Cryptic, hash, Address
from enum import Enum
from asyncio import Future


class Wallet:
    def __init__(self, name):
        self.name = name
        self.key = Key(name)
        self.public = self.key.get_public()
        self.address = Address.get(self.public)
        Cryptic.add("s_"+self.name, self.key.secret)
        Cryptic.add("p_"+self.name, self.public.pubkey)
        Cryptic.add("#"+self.name, self.address.value)
      
    def get_public(self):
        return self.public
    
    def get_address(self):
        return self.address
    
    def sign(self, msg):
        return self.key.sign(msg)
    



class Parameters:
    def __init__(self, prefix : str = "$$"):
        self.data = {}
        self.vars = set()
        self.cnt = 0
        self.prefix = prefix

    def apply(self, obj : any):
        if isinstance(obj, int):
            return obj
        elif isinstance(obj, str):
            if obj.startswith(self.prefix) and obj in self.vars:
                return self[obj]    
            return obj
        elif isinstance(obj, list):
            return [self.apply(x) for x in obj]
        
        return obj.apply(self)


    def var(self, var : Optional[str] = None):
        if var is None:
            var = "var"+str(self.cnt)
            self.cnt += 1

        if not var.startswith(self.prefix):
            var = self.prefix+var

        if var not in self.vars:
            self.vars.add(var)

        return var

    def __setitem__(self, key : str, value : any):
        if not key.startswith(self.prefix):
            key = self.prefix+key

        self.data[key] = value

    def __getitem__(self, key):
        if not key.startswith(self.prefix):
            key = self.prefix+key
        
        return self.data[key]
    
    def __contains__(self, key):
        if not key.startswith(self.prefix):
            key = self.prefix+key

        return key in self.vars
    
    

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

    def transfer(self, source : Wallet, destination : Wallet, amount : int) -> Transaction:
        pass

    def sweep(self, user : Wallet) -> Transaction:
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
