from enum import Enum
from mockchain.crypto import hash, commit, Key, Public
from typing import List, Optional, Union
from mockchain.user import User


Address = Union[str, User, Public]

def get_public(addr : Address ) -> Address:
    if type(addr) is str:
        return Key.publics[addr]
    elif type(addr) is User:
        return addr.get_public()
    else:
        return addr
    

class Operation:
    def __init__(self, opcode : str, args : List[str]):
        self.opcode = opcode
        self.args = args

    def __str__(self):
        return self.opcode + "(" + ", ".join([str(arg) for arg in self.args]) + ")"
    
    def __repr__(self):
        return self.opcode + "(" + ", ".join([str(arg) for arg in self.args]) + ")"
    
    @staticmethod
    def check_sig(addr : Address):
        addr = get_public(addr)

        return Operation("check_sig", [addr])
    
    @staticmethod
    def check_multisig(addresses, min=1):
        args = [min, len(addresses)]
        addresses = [ get_public(addr) for addr in addresses]

        args.extend(addresses)
        return Operation("check_multisig", args)

    @staticmethod
    def reveal(hashes : List[str]):
        return Operation("reveal", hashes)
    
    @staticmethod
    def equivocation(hashes : List[str]):
        return Operation("equivocation", hashes)

    @staticmethod
    def timelock(sequence : int):
        return Operation("timelock", [sequence])


class Script:
    def __init__(self, script : List[Operation]):
        self.script = script

    @staticmethod
    def p2pubkey(addr : Address):
        return Script([Operation.check_sig(get_public(addr))])
    
    @staticmethod
    def p2timelock(sequence : int, addr : Optional[Address]):
        if addr is None:
            return Script([Operation.timelock(sequence)])
        else:
            return Script([Operation.check_sig(get_public(addr)), Operation.timelock(sequence)])
    
    @staticmethod
    def p2reveal(hashes : List[str], addr : Optional[Address]):
        if addr is None:
            return Script([Operation.reveal(hashes)])
        else:
            if type(addr) is str:
                addr = Key.publics[addr]
            elif type(addr) is User:
                addr = addr.get_public()
        
            return Script([Operation.check_sig(get_public(addr)), Operation.reveal(hashes)])


    def __str__(self):
        return "{"+" ".join([op.__str__() for op in self.script])+"}"

    def __repr__(self):
        return "{"+" ".join([op.__repr__() for op in self.script])+"}"
    
    def is_p2pubkey(self, addr : Address):
        addr = get_public(addr)
        return len(self.script) == 1 and self.script[0].opcode == "check_sig" and self.script[0].args[0] == addr
    
    def run(self, stack, tx):
        for op in self.script:
            if op.opcode == "check_sig":
                sig = stack.pop(0)
                pubkey = op.args[0]
                if pubkey is str:
                    pubkey = Public.publics[pubkey]

                if pubkey.verify(tx.hash, sig) == False:
                    return False
                
            elif op.opcode == "check_multisig":
                cnt = op.args[0]
                pubkeys = op.args[2:]

                sig = stack.pop(0)
                    
                for pub in pubkeys:
                    if pub.verify(tx.hash, sig) == True:
                        cnt -= 1
                        if cnt == 0:
                            break
                        sig = stack.pop(0)
                        continue
                    
                if cnt == 0: 
                    return False
                
            elif op.opcode == "reveal":
                preimage = stack.pop(0)

                valid = False

                for h in op.args:
                    if h == commit(preimage):
                        valid = True
                
                if not valid:
                    return False
            
            elif op.opcode == "equivocation":
                preimage = stack.pop(0)
                cnt = 0

                for h in op.args:
                    if h == commit(preimage):
                        cnt += 1
                        if cnt == 2:
                            break
                        preimage = stack.pop(0)

                if cnt != 2:
                    return False
                
            elif op.opcode == "timelock":
                sequence = self.output.sequence + int(op.args[0])

                if sequence > tx.sequence:
                    return False
            else:
                raise Exception("Unknown opcode")
            
        return True         
    


class Output:
    def __init__(self, amount : int, scripts : Script | List[Script]):
        if  not isinstance(scripts,list):
            scripts = [scripts]

        for script in scripts:
            script.output = self

        self.amount = amount
        self.scripts = scripts
        self.sequence = 0
        self.hash = hash(str(self))
    

    def __str__(self):
        return "$"+str(self.amount)+" ["+", ".join([str(script) for script in self.scripts])+"]"

    def __repr__(self):
        return "$"+str(self.amount)+" ["+", ".join([str(script) for script in self.scripts])+"]"

    def is_p2pubkey(self, addr : Address):
        addr = get_public(addr) 

        for script in self.scripts:
            if script.is_p2pubkey(addr):
                return True
        return False
    
    def satisfy(self, leaf : int, witness : List[str], tx) -> bool:
        stack = witness.copy()
        script = self.scripts[leaf]
        if script.run(stack, tx) == False:
            return False
            
        return True



class Input:
    def __init__(self, ptr : str, leaf : int = 0):
        self.ptr = ptr
        self.leaf = leaf
        self.witness = [] 

    def set_witness(self, witness : List[str]):
        self.witness = witness

    def is_p2pubkey(self, addr : Address):
        addr = get_public(addr)

        return self.leaf == 0 and self.witness[0] == addr
    

    def __str__(self):
        ptr = self.ptr
        if self.leaf != 0:
            ptr += "." + str(self.leaf)

        return ptr + " ["+", ".join([str(w) for w in self.witness])+"]"
    
    def __repr__(self):
        ptr = self.ptr
        if self.leaf != 0:
            ptr += "." + str(self.leaf)

        return ptr + " ["+", ".join([str(w) for w in self.witness])+"]"
    

class TransactionStatus(Enum):
    CREATED = "created"
    SIGNED = "signed"
    PARTIALLY_SIGNED = "partially_signed"
    CONFIRMED = "confirmed"
    FAILED = "failed"

    def __str__(self):
        return self.value

class Transaction:
    def __init__(self, blockchain : "Blockchain", inputs : List[Input|str], outputs : List[Output]):
        inputs = [input if type(input) is Input else Input(input) for input in inputs]

        self.blockchain = blockchain
        self.inputs = inputs
        self.outputs = outputs
        self.status = TransactionStatus.CREATED

        txdata = ",".join([input.ptr for input in inputs]) + " -> " + ",".join([str(output.amount)+":"+output.hash for output in outputs])
        self.hash = hash(str(txdata))
    
    def __str__(self):
        return "TX ["+", ".join(str(input.ptr) for input in self.inputs)+"] -> ["+", ".join([str(output) for output in self.outputs])+"] ("+self.status+")"
    
    def __repr__(self):
        return "TX ["+", ".join(str(input.ptr) for input in self.inputs)+"] -> ["+", ".join([str(output) for output in self.outputs])+"] ("+self.status+")"
   
    def sign(self, user : User ):
        signature = user.sign(self.hash)
        satisfied = True

        for input in self.inputs:
            if input.ptr not in self.blockchain.utxo_set:
                raise Exception("input not found")
            
            output = self.blockchain.utxo_set[input.ptr]
            if input.leaf < 0 or input.leaf >= len(output.scripts):
                raise Exception("invalid leaf")
            
            script = output.scripts[input.leaf]

            if script.is_p2pubkey(user):
                input.witness.append(signature)
            else:
                satisfied = False
    
        if satisfied:
            self.status = TransactionStatus.SIGNED
        else:
            self.status = TransactionStatus.PARTIALLY_SIGNED

        return satisfied
    


class Blockchain:
    def __init__(self, faucet : User = None, capacity : int = 1000000, block_reward : int = 50):
        if faucet is None:
            faucet = User('faucet')

        self.faucet = faucet

        genesis = Output(capacity,  Script.p2pubkey(faucet))
        genesis.ptr = "genesis:0"
        genesis.sequence = -1
        self.sequence = 0
        self.block_reward = block_reward

        self.utxo_set = {genesis.ptr : genesis}
        self.mempool = []
        self.blocks = []
        
    
    def create_transaction(self, inputs : List[Input|str], outputs : List[Output]):
        return Transaction(self, inputs, outputs)
    

    def add_transaction(self, transaction : Transaction):
        self.mempool.append(transaction)

    def mine_transaction(self, transaction : Transaction, check_inputs=True): 
        if transaction.status == TransactionStatus.CONFIRMED:
            transaction.status_msg = "already mined"
            return False
        
        
        allocated = sum([output.amount for output in transaction.outputs])
        amount = 0

        transaction.sequence = self.sequence
        if check_inputs:
            for input in transaction.inputs:
                ptr = input.ptr

                if ptr not in self.utxo_set:
                    transaction.status_msg = "input not found: "+ptr
                    transaction.status = TransactionStatus.FAILED
                    return False
                
                output = self.utxo_set[ptr]
                if output.satisfy(input.leaf, input.witness, transaction) == False:
                    transaction.status_msg = "input not satisfied by witness: "+ ptr
                    transaction.status = TransactionStatus.FAILED
                    return False
                
                amount += output.amount    
            
        
            if amount < allocated:
                transaction.status_msg = "insufficient funds"
                transaction.status = TransactionStatus.FAILED
                return False
        
        for input in transaction.inputs:
            del self.utxo_set[input.ptr]
            
        
        outputs = transaction.outputs
        
        if amount > allocated:
            change = Output(amount-allocated,  Script.p2pubkey(self.faucet))
            outputs.append(change)

        for i in range(len(outputs)):
            output = outputs[i]
            output.ptr = transaction.hash+":"+str(i)
            output.sequence = self.sequence
            self.utxo_set[output.ptr] = output

        transaction.status = TransactionStatus.CONFIRMED
        return True


    def UTXOs_for_address(self, addr : Address):
        return [ key for key, output in self.utxo_set.items() if output.is_p2pubkey(addr)]
                
    
    def transfer(self, source : User, destination : User, amount : int):
        utxos = self.UTXOs_for_address(source)
        
        inputs = []
        
        total = 0
        for ptr in utxos:
            output = self.utxo_set[ptr]
            inputs.append(Input(ptr))

            total += output.amount
            if total >= amount:
                break
        
        if total < amount:
            raise Exception("insufficient funds")
        
        output = Output(amount, Script.p2pubkey(destination))
        change = Output(total-amount, Script.p2pubkey(source))
        tx = self.create_transaction(inputs, [output, change])
        tx.sign(source)
        return tx
    
    def sweep(self, user : User):
        utxos = self.UTXOs_for_address(user)
        total = sum([self.utxo_set[ptr].amount for ptr in utxos])

        output = Output(total, Script.p2pubkey(user))
        tx = self.create_transaction([Input(ptr) for ptr in utxos], [output])
        tx.sign(user)
        return tx
    

    def mine_blocks(self, cnt=1, miner : Address = None):
        for _ in range(cnt):
            block = []
            
            if miner != None:
                tx = self.create_transaction([], [Output(self.block_reward, Script.p2pubkey(miner))])
                if self.mine_transaction(tx, check_inputs=False):
                    tx.txnum = len(block)
                    block.append(tx)
                
            for tx in self.mempool:
                if self.mine_transaction(tx) == True:
                    tx.txnum = len(block)
                    block.append(tx)
            
            self.blocks.append(block)
            self.sequence += 1
            self.mempool = []

    def __str__(self):
        return "["+", ".join([str(output) for output in self.utxo_set])+"]"

    def __repr__(self):
        return "["+", ".join([str(output) for output in self.utxo_set])+"]"