from mockchain.blockchain import  Wallet, TransactionStatus
from mockchain.crypto import Cryptic, Address
from mockchain.bitcoin import Bitcoin, BitcoinTransaction, Input, Output
from typing import List, Optional, Dict

class Protocol:
    def __init__(self):
        self.variables = {}
        self.users = []
        self.transactions = []
        self.anon_var = 0
        self.prefix = "$"
 
    def apply(self, param : Optional[Dict[str, any]] = None):
        if param is not None:
            self.variables.update(param)
            
        transactions = []

        for i in range(len(self.transactions)):
            tx = self.transactions[i]
            transactions.append(tx.apply(self))
            self.set(self.tx_var(i), transactions[i].hash)

        return transactions
          


    def tx_var(self, index : Optional[int] = None) -> int:
        if index is None:
            return self.var("tx"+str(len(self.transactions)))
            
        return self.var("tx"+str(index))
        

    def create_transaction(self, inputs : List[Input], outputs : List[Output]):
        tx = BitcoinTransaction(self, inputs, outputs)

        hash = self.tx_var()
        self.transactions.append(tx)
        tx.hash = hash

        index = 0
        for output in tx.outputs:
            output.hash = hash+"."+str(index)
            index += 1

        return tx

    def with_prefix(self, name : str) -> str:
        if not name.startswith(self.prefix):
            name = self.prefix + name

        return name
    
    def user(self, name : Optional[str] = None):
        if name is None:
            name = "user"+str(len(self.users))

        name = self.with_prefix(name)

        if name not in self.users:
            self.users.append(name)
            if name in self.variables:
                raise Exception(f"Variable {name} already exists")
            self.variables[name] = name

        return name
    
    def var(self, name : Optional[str] = None) -> str:
        if name is None:
            name = "var"+str(self.anon_var)
            self.anon_var += 1

        name = self.with_prefix(name)

        if name not in self.variables:
            self.variables[name] = name
        
        return name

    def set(self, name : str, value : any):
        name = self.with_prefix(name)
        self.variables[self.var(name)] = value

    def get(self, obj : any) -> any:
        if isinstance(obj, str):
            return self.variables.get(self.with_prefix(obj), obj)
        
        return obj
    
