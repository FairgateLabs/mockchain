from enum import Enum
from mockchain.crypto import hash, commit, Key, Public, Cryptic, Address
from typing import List, Optional, Union, Dict, Tuple, Callable
from mockchain.blockchain import User, Transaction, TransactionStatus, Blockchain 


PolicyId = str
TokenName = str
Datum = Optional[str]
Script = Optional[Callable]
TimeRange = Optional[Tuple]


class Value:
    def __init__(self, value : Dict[PolicyId, Dict[TokenName, int]] = {}):
        self.value = value

    @staticmethod
    def ADA(amount : int):
        return Value({"": {"ADA": amount}})
    
    @staticmethod
    def Token(policy : PolicyId, token : TokenName, amount : int):
        return Value({policy: {token: amount}})
    
    def __iter__(self):
        for policy, tokens in self.value.items():
            for token, amount in tokens.items():
                yield policy, token

        return iter(self.value)
    

    def items(self):
        for policy, tokens in self.value.items():
            for token, amount in tokens.items():
                yield policy, token, amount

        return iter(self.value)
    
    def __getitem__(self, key):
        if type(key) is tuple:
            if key[0] in self.value and key[1] in self.value[key[0]]:
                return self.value[key[0]][key[1]]
            else:
                return 0
        else:
            if key in self.value:
                return self.value[key]
            else:
                return {}
            
    def __setitem__(self, key, value):
        if type(key) is tuple:
            if key[0] not in self.value:
                self.value[key[0]] = {}
            self.value[key[0]][key[1]] = value
        else:
            self.value[key] = value
            
    def __add__(self, other):
        value = {}

        for policy, token, amount in self.items():
            if policy not in value:
                value[policy] = {}
            if token not in value[policy]:
                value[policy][token] = 0
            value[policy][token] = amount
        
        for policy, token, amount in other.items():
            if policy not in value:
                value[policy] = {}
            if token not in value[policy]:
                value[policy][token] = 0
            value[policy][token] += amount
        
        return Value(value)
    
    def __sub__(self, other):
        value = {}

        for policy, token, amount in self.items():
            if policy not in value:
                value[policy] = {}
            if token not in value[policy]:
                value[policy][token] = 0
            value[policy][token] = amount
        
        for policy, token, amount in other.items():
            if policy not in value:
                value[policy] = {}
            if token not in value[policy]:
                value[policy][token] = 0
            value[policy][token] -= amount
        
        return Value(value)
    
    def __str__(self):
        v = ""
        for policy, token, amount in self.items():
                if len(v) > 0:
                    v += ", "

                policy_str = Cryptic.get(policy)
                v += f"{policy_str}.{token}:{amount}"
        return v
    
    def __repr__(self):
        return str(self)
    

class ScriptPurpose(Enum):
    Minting = "minting"
    Spending = "spending"
    Rewarding = "rewarding"
    Certifying = "certifying"

    def __repr__(self):
        return self.value
    
    def __str__(self):
        return self.value

class ScriptContext:
    def __init__(self, purpose : ScriptPurpose, transaction : "Transaction", policy : PolicyId | None = None):
        self.purpose = purpose
        self.txinfo = transaction
        self.policy = policy
        self.txout = None

class Output:
    def __init__(self, address : Address, value : Value | int, datum : Datum = None):
        if type(value) is int:
            value = Value.ADA(value)

        address = Address.get(address)
        self.address = address

        if address.is_script:
            self.script = address.script
        else:
            self.script = None

        self.value = value
        self.datum = datum
    
    def satisfy(self, transaction : "CardanoTransaction" ) -> bool:
        if self.script is not None:
            context = ScriptContext(ScriptPurpose.Spending, transaction, None)
            context.txout = self

            if not self.script(transaction.redeemers, context):
                return False
            
        if not self.address.is_script:
            if self.address not in transaction.signatories:
                return False
            
        return True
    
    def __str__(self):
        v = str(self.value)+ " -> " + str(self.address)
        if self.datum is not None:
            v +="("+str(self.datum)+")"
        return v
    
    def __repr__(self):
        return str(self)


class Input:
    def __init__(self, ptr : str):
        self.ptr = ptr
        self.reference = None
        
    def __str__(self):
        return self.ptr
    
            
    def __repr__(self):
        return self.ptr


class CardanoTransaction(Transaction):
    def __init__(self, blockchain : "Cardano", inputs : List[Input|str], outputs : List[Output], reference_inputs: List[Input|str] = None, mint: Value = None):
        inputs = [input if type(input) is Input else Input(input) for input in inputs]
 
        for output in outputs:
            if not isinstance(output, Output):
                raise Exception("Invalid output")
            
        if reference_inputs is not None:
            reference_inputs = [input if type(input) is Input else Input(input) for input in reference_inputs]
        
        if mint is None:
            mint = Value()

        self.blockchain = blockchain
        self.inputs = inputs
        self.reference_inputs = reference_inputs
        self.outputs = outputs
        self.mint = mint
        self.time_range = None
        self.signatures = []
        self.signatories = []
        self.redeemers = {}
        self.status = TransactionStatus.CREATED

        txdata = ",".join([input.ptr for input in self.inputs]) + ") -> (" + ",".join([str(output) for output in self.outputs]) 
        self.hash = hash(str(txdata))

        for i in range(len(self.outputs)):
            output = self.outputs[i]
            output.ptr = self.hash+":"+str(i)
    
    
    def __str__(self):
        return  Cryptic.get(self.hash) + " (" + ",".join([Cryptic.get(input.ptr) for input in self.inputs]) + ") -> (" + ",".join([str(output) for output in self.outputs]) + ")" + self.status.value
    
    def __repr__(self):
        return  Cryptic.get(self.hash) + " (" + ",".join([Cryptic.get(input.ptr) for input in self.inputs]) + ") -> (" + ",".join([str(output) for output in self.outputs]) + ")" + self.status.value
    
    def add_signature(self, signature : str, address : Address):
        self.signatures.append(signature)
        self.signatories.append(address)
        self.status = TransactionStatus.SIGNED
        
    def sign(self, user : User):
        signature = user.sign(self.hash)
        self.add_signature(signature, user.get_address())
 
        return True
    
    def set_time_range(self, time_range : TimeRange):
        self.time_range = time_range

    def set_redeemer(self, policy : PolicyId, redeemer):
        self.redeemers[policy] = redeemer
    


class Cardano(Blockchain):
    def __init__(self, faucet : User = None, supply : int = 1000000, block_reward : int = 50):
        super().__init__()
        
        self.name = "cardano"
        if faucet is None:
            faucet = User('cardano-faucet')

        self.faucet = faucet

        genesis = Output(faucet, Value.ADA(supply), None)
        genesis.ptr = "genesis:0"
        genesis.sequence = -1

        self.height = 0
        self.block_reward = block_reward
        self.supply = supply

        self.utxo_set = {genesis.ptr : genesis}
        self.mempool = []
        self.blocks = []
        self.policies = {}
        self.transaction_dict = {}

    
    def add_policy(self, script : Script) -> PolicyId:
        if script is None:
            return None
        
        # calculate hash of script
        policy = hash(str(script.__code__.co_code))
        Cryptic.add("pol"+str(len(self.policies)), policy)
        self.policies[policy] = script
        return policy
    
    def get_transaction(self, hash : str):
        return self.transaction_dict.get(hash,None)
    
    def create_transaction(self, inputs : List[Input|str], outputs : List[Output], reference_inputs : List[Input|str] = None, mint : Value = None):
        return CardanoTransaction(self, inputs, outputs, reference_inputs, mint)
    
    def create_mint_transaction(self, mint : Value, destination : Address):
        return CardanoTransaction(self, [], [Output(destination, mint)], mint=mint)
    
    def add_transaction(self, transaction : CardanoTransaction, name : Optional[str] = None):
        if name is None:
            name = "tx"+str(len(self.transaction_dict))

        Cryptic.add(name, transaction.hash)

        for i in range(len(transaction.outputs)):
            si = str(i)
            Cryptic.add(name+":"+si, transaction.hash +":"+si)
        
        self.mempool.append(transaction)
        self.transaction_dict[transaction.hash] = transaction

    def mine_transaction(self, transaction : CardanoTransaction, check_inputs=True): 
        if transaction.status == TransactionStatus.CONFIRMED:
            transaction.status_msg = "already mined"
            return False
        
        if len(transaction.signatures) != len(transaction.signatories):
            transaction.status_msg = "invalid signature count"
            transaction.status = TransactionStatus.FAILED
            return False
        
        for i in range(len(transaction.signatures)):
            if not transaction.signatories[i].verify(transaction.hash, transaction.signatures[i]):
                transaction.status_msg = "invalid signature"
                transaction.status = TransactionStatus.FAILED
                return False
            
        
        allocated = Value()

        for output in transaction.outputs:
            allocated += output.value

        amount = transaction.mint    
        transaction.sequence = self.height

        for policy, tokens in transaction.mint.value.items():
            if policy == "" or len(tokens) == 0: 
                continue

            if policy not in self.policies:
                transaction.status_msg = "policy not found: "+policy
                transaction.status = TransactionStatus.FAILED
                return False
            
            context = ScriptContext(ScriptPurpose.Minting, transaction, policy)
            redeemer = transaction.redeemers[policy] if policy in transaction.redeemers else None

            if not self.policies[policy](redeemer, context):
                transaction.status_msg = "minting policy failed: "+policy
                transaction.status = TransactionStatus.FAILED
                return False

        if check_inputs:
            for input in transaction.inputs:
                ptr = input.ptr

                if ptr not in self.utxo_set:
                    transaction.status_msg = "input not found: "+ptr
                    transaction.status = TransactionStatus.FAILED
                    return False
                
                output = self.utxo_set[ptr]
                input.reference = output
                if output.satisfy(transaction) == False:
                    transaction.status_msg = "input not satisfied: "+ ptr
                    transaction.status = TransactionStatus.FAILED
                    return False
                
                amount += output.value    
            
            for policy, token in amount:
                if amount[(policy, token)] < allocated[(policy, token)]:
                    transaction.status_msg = "insufficient funds"
                    transaction.status = TransactionStatus.FAILED
                    return False
        
        for input in transaction.inputs:
            del self.utxo_set[input.ptr]
            
        for i in range(len(transaction.outputs)):
            output = transaction.outputs[i]
            output.ptr = transaction.hash+":"+str(i)
            output.sequence = self.height
            self.utxo_set[output.ptr] = output

        
        transaction.status = TransactionStatus.CONFIRMED
        return True
    
    def mine_block(self, cnt=1, miner : Address = None):
        for _ in range(cnt):
            block = []
            
            if miner != None:
                tx = self.create_transaction([], [Output(miner, Value.ADA(self.block_reward), None)])
                if self.mine_transaction(tx, check_inputs=False):
                    tx.txnum = len(block)
                    block.append(tx)
                
            for tx in self.mempool:
                if self.mine_transaction(tx) == True:
                    tx.txnum = len(block)
                    block.append(tx)
            
            self.blocks.append(block)
            self.mempool = []

            self.notify(block)
            
            self.height += 1


    def UTXOs_for_address(self, addr : Address):
        addr = Address.get(addr)
        return [ key for key, output in self.utxo_set.items() if output.address == addr]
                
    
    def transfer(self, source : User, destination : User, amount : Value | int):
        utxos = self.UTXOs_for_address(source)
        
        if type(amount) is int:
            amount = Value.ADA(amount)

        inputs = []
        total = Value()

        for ptr in utxos:
            output = self.utxo_set[ptr]
            
            for policy,token in output.value:
                if total[(policy, token)] < amount[(policy, token)]:
                    inputs.append(Input(ptr))
                    total += output.value
                    break
        
        change_value = total - amount
        need_change = False

        for policy, token in change_value:
            left = total[(policy, token)] - amount[(policy, token)]
            if left < 0:
                raise Exception("insufficient funds")
            
            if left > 0:
                need_change = True
                
            
        output = Output(destination, amount)
        change = Output(source, change_value)

        if need_change:
           tx = self.create_transaction(inputs, [output, change])
        else:
            tx = self.create_transaction(inputs, [output])

        tx.sign(source)

        return tx
    
    def sweep(self, user : User):
        utxos = self.UTXOs_for_address(user)
        total = sum([self.utxo_set[ptr].value for ptr in utxos])

        output = Output(user, total)
        tx = self.create_transaction([Input(ptr) for ptr in utxos], [output])
        tx.sign(user)
        return tx
    
    def print(self, block_height : Optional[int] = None):
        start = 0
        end = len(self.blocks)

        if block_height is not None:
            start = block_height
            end = block_height+1

        for i in range(start, end):
            print(f"Cardano Block {i} -----------------------------------------")
            for tx in self.blocks[i]:
                print(f"  {tx}")

    def print_utxos(self):
        for utxo in self.utxo_set:
            print(Cryptic.get(utxo), self.utxo_set[utxo])


    def __str__(self):
        return f'{self.name} -- blocks: {len(self.blocks)} mempool: {len(self.mempool)} UTXOs: {len(self.utxo_set)}'

    def __repr__(self):
        return f'{self.name} -- blocks: {len(self.blocks)} mempool: {len(self.mempool)} UTXOs: {len(self.utxo_set)}'
    
