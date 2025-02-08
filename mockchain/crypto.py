import hashlib


n = 5163163205333349429433481553

def hash(msg):
    return hashlib.sha256(msg.encode("utf8")).hexdigest()[0:20]

def number_from_hex(hex):
    return int(hex, 16) % n


class Secret:
    def __init__(self, seed):
        self.seed = seed
        self.index = 0

    def next(self):
        self.index += 1
        return self.get(self.index)

    def get(self, index):
        return hash(self.seed+"_"+str(index))
    

class Key:
    publics = {}
    def __init__(self, key):
        self.key = key
        self.ciphertext = {}
        Key.publics[self.key] = Public(self)

    def public(self):
        return Key.publics[self.key]

    def sign(self,msg):
        sign = "$"+hash(self.key+":"+msg)[0:20]
        return sign

    def verify(self, msg, signature):
        h = hash(msg)

        sign = "$"+hash(self.key+":"+msg)[0:20]
        return sign == signature

    def encrypt(self, msg):
        cipher = "#"+hash(self.key+":"+msg)[0:20]
        self.ciphertexts[cipher] = msg
        return cipher
    
    def decrypt(self, cipher):
        if cipher in self.ciphertexts:
            return self.ciphertexts[cipher]
        else:
            raise Exception("unknown ciphertext")
        
    def __repr__(self) -> str:
        return "key_"+self.key
    

class Public:
    def __init__(self, private):
        self.private = private

    def public(self):
        return self
    
    def sign(self, msg):
        raise Exception("Cannot sign with public key")
    
    def decrypt(self, msg):
        raise Exception("Cannot decrypt with public key")
    
    def verify(self, msg, signature):
        return self.private.verify(msg, signature)
    
    def encrypt(self, msg):
        return self.private.encrypt(msg)
    
    def __repr__(self):
        return self.private.key
    

def commit(msg):
    return Commitment.commit(msg)


class Commitment:
    commitments = {}

    @staticmethod
    def commit(msg):
        Commitment.commitments[msg] = "h_"+msg
        return "h_"+msg
