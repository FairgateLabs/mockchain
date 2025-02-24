import hashlib
from typing import List, Callable
from types import CodeType, FunctionType, MethodType

Signature = int

N = 10000000001141
G = 2

Script=Callable

def hash(msg):
    return hashlib.sha256(msg.encode("utf8")).hexdigest()[0:20]

def number_from_hex(hex):
    return int(hex, 16) % N

class Cryptic:
    names = {}
    values = {}

    @staticmethod
    def add(name, value):
        Cryptic.names[value] = name
        Cryptic.values[name] = value

    @staticmethod
    def get(value):
        if value in Cryptic.names:
            return str(Cryptic.names[value])
        return str(value)
    

class Secret:
    seed = "seed"
    index = 0

    @staticmethod
    def next():
        Secret.index += 1
        return Secret.get(Secret.index)
    
    def number():
        return number_from_hex(Secret.next()) 

    @staticmethod
    def get(index):
        return hash(Secret.seed+"_"+str(index))
    

class Key:
    def __init__(self, name : str):
        self.name = name
        self.secret = Secret.number()
        self.public = Public.from_secret(self.secret)  

    def get_public(self):
        return self.public

    def sign(self,msg : str) -> Signature:
        h = number_from_hex(hash(msg))
        k = Secret.number()
        r = pow(G, k, N)
        s = (k + self.secret * h) % (N-1)
        sign = (r, s)
        return sign

    def verify(self, msg : str, signature : Signature) -> bool:
        return self.get_public().verify(msg, signature)

    def encrypt(self, msg : int) -> int:
        return (msg - self.secret + N) % N
    
    def decrypt(self, cipher):
        return (cipher + self.secret) % N

    def __repr__(self) -> str:
        return "key_"+self.name
    


class Public:
    def __init__(self, pubkey : int):
        self.pubkey = pubkey
        self.address = Address.get(self)

    @staticmethod
    def from_secret(secret):
        return Public(pow(G, secret, N))
     
    def get_public(self):
        return self
    
    def sign(self, msg):
        raise Exception("Cannot sign with public key")
    
    def decrypt(self, msg):
        raise Exception("Cannot decrypt with public key")
    
    def verify(self, msg : str, signature : Signature) -> bool:
        h = number_from_hex(hash(msg))
        r,s = signature

        G1 = pow(G, s, N)
        G2 = (r * pow(self.pubkey, h, N)) % N
        return G1 == G2
    
    def encrypt(self, msg : int) -> int:
        return (msg + self.pubkey) % N
         
    def __repr__(self):
        return Cryptic.get(self.pubkey)



class Address:
    cache = {}

    @staticmethod 
    def get_str(source) -> str:
        if isinstance(source, str):
            return source
        
        return Address.get(source).value
    
    @staticmethod
    def get(source) -> "Address":
        if type(source) is int:
            source = hex(source)

        if type(source) is str:
            if source in Address.cache:
                return Address.cache[source]
            
            raise Exception("Address not found")
        
        if type(source) is Address:
            return source
        
        source = source.get_public()

        if isinstance(source,Public):
            if source.pubkey in Address.cache:
                return Address.cache[source.pubkey]
            
            hashcode = hash("public+"+hex(source.pubkey))
            address = Address(source, hashcode, False)
            Address.cache[source.pubkey] = address
            return address
   
        raise Exception("Invalid address source")
    
    def verify(self, msg, signature):
        if self.is_script:
            raise Exception("Cannot verify with script address")
        
        return self.public.verify(msg, signature)
    
    def __init__(self, source : any, hash : str, is_script : bool):
        self.value = hash
        self.is_script = is_script

        if is_script:
            self.program = source
        else:
            if not isinstance(source, Public):
                raise Exception("Invalid source")
        
            self.public = source
        
        Address.cache[self.value] = self
        

    def __str__(self):
        return Cryptic.get(self.value)
    
    def __repr__(self):
        return Cryptic.get(self.value)
    
 
class AggregatePublic(Public):
    def __init__(self, name : str, publics : List[Public]):
        self.name = name

        pubkeys = [x.get_public().pubkey for x in publics]
        pubkeys.sort()

        self.coef = number_from_hex(hash(",".join(map(str, pubkeys))))

        z = 1
        for p in pubkeys:
            p = pow(p, self.coef, N)
            z = (z * p) % N

        self.pubkey = z
        self.address = Address.get(self)

        Cryptic.add("@"+self.name, self.pubkey)
        Cryptic.add("#"+self.name, self.address.value)

    def aggregate(self, signatures : List[Signature]) -> Signature:
        r = 1
        s = 0

        for p in signatures:
            r = (r * pow(p[0], self.coef, N)) % N
            s = (s + p[1] * self.coef) % (N-1)

        return (r,s)


def commit(msg):
    return Commitment.commit(msg)


class Commitment:
    @staticmethod
    def commit(msg):
        commitment = hash(msg)
        Cryptic.add("h_"+msg, commitment)

        return commitment

class TransferOfOnwership:
    def __init__(self, publics : List[Public]):
        self.publics = publics
        self.groups = []

        self.n = len(publics)
        self.k = 2 ** self.n

        for i in range(self.k):
            group = []
            for j in range(self.n):
                if i & (1 << j):
                    group.append(publics[j])

            if len(group) > 0:
                self.groups.append(AggregatePublic('gid_'+str(i), group))
            else:
                self.groups.append(None)
    
        