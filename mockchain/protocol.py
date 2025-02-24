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
        self.prefix_len = len(self.prefix)
        self.params = {}
        self.indexes = {}
        

    def reset(self):
        self.params = {}
        self.indexes = {}


    def apply(self, param : Optional[Dict[str, any]] = None):
        if param is not None:
            self.variables.update(param)
            
        transactions = []

        for i in range(len(self.transactions)):
            orig_tx = self.transactions[i]
            self.reset()

            tx_versions = []
            
            hashes = []
            while(True): 
                tx = orig_tx.apply(self)
                tx_versions.append(tx)
                hashes.append(tx.hash)
                if not self.next():
                    break
            
            transactions.append(tx_versions)
            self.set(self.tx_var(i), hashes)

        self.reset()
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

        self.variables[name] = value

    def next(self):
        for k in self.indexes:
            self.indexes[k] += 1
            if self.indexes[k] < len(self.params[k]):
                return True
            self.indexes[k] = 0
        return False
            

    def get(self, obj : any) -> any:
        if isinstance(obj, str) and obj.startswith(self.prefix):
            var = obj
            if var in self.params:
                return self.params[var][self.indexes[var]]
            
            hlevel = var.split("|")
            options = []
            for v in hlevel:
                vv = v.split(":")
                v0 = vv[0]
                if len(vv) > 1:
                    v1 = ":"+vv[1]
                else:
                    v1 = ""

                llevel = self.variables[v0]

                if not isinstance(llevel, list):
                    llevel = [llevel]

                for option in llevel:
                    if isinstance(option, str):
                        options.append(option+v1)
                    else:
                        options.append(option)
                
            self.params[var] = options
            self.indexes[var] = 0
            return options[0]
        else:
            return obj
    
