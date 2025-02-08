from mockchain.crypto import Secret, Key

class User:
    def __init__(self, name):
        self.name = name
        self.secret = Secret(name + " secret")
        self.key = Key(name)
        self.public = self.key.public()

    def get_public(self):
        return self.public
    
    def sign(self, hash):
        return self.key.sign(hash)