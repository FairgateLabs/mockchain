import unittest
from mockchain.crypto import hash, AggregatePublic, Public, Key, TransferOfOnwership, commit, Cryptic, G, N

class TestHash(unittest.TestCase):  
    def test_hash(self):
        self.assertEqual(hash("test"), "9f86d081884c7d659a2f")
        
  

class TestKey(unittest.TestCase):
    def test_create(self):
        k = Key('1')
        pk = k.get_public()

        self.assertEqual(k.name, '1')
        self.assertEqual(pk.pubkey, pow(G, k.secret, N))

    def test_sign(self):
        k = Key('1')
        pk = k.get_public()
        
        msg = 'msg'
        msg2 = 'other message'

        sign = k.sign(msg)
        self.assertTrue(k.verify(msg, sign))
        self.assertFalse(k.verify(msg2, sign))



class TestAggregateKey(unittest.TestCase):
    def test_create(self):
        k1 = Key('1')
        k2 = Key('2')

        apk = AggregatePublic('ak', [k1.get_public(), k2.get_public()])
        self.assertEqual(apk.name, 'ak')
        
    def test_aggregate_signatures(self):
        k1 = Key('1')
        k2 = Key('2')
        msg = 'msg'
        apk = AggregatePublic('ak', [k1.get_public(), k2.get_public()])
        s1 = k1.sign(msg)
        s2 = k2.sign(msg)
        ag_sign = apk.aggregate([s1, s2])
        self.assertTrue(apk.verify(msg, ag_sign))
        

class TestTransferOfOwnership(unittest.TestCase):
    def test_create(self):
        k = [Key(x) for x in ['1','2','3','4'] ]
        pk = [x.get_public() for x in k]
        too = TransferOfOnwership(pk)
        self.assertEqual(too.n, len(k))
        self.assertEqual(too.k, 2**len(k))
        
    def test_pubkey(self):
        k = [Key(x) for x in ['1','2','3','4'] ]
        pk = [x.get_public() for x in k]
        too = TransferOfOnwership(pk)
        apk = AggregatePublic('ak', pk)

        self.assertEqual(apk.pubkey, too.groups[-1].pubkey)




class TestCommit(unittest.TestCase):
    def test_commit(self):
        m1 = "hello"
        m2 = "goodbye"
        h1 = commit(m1)
        h2 = commit(m2)

        self.assertEqual(h1, "h_hello")
        self.assertEqual(h2, "h_goodbye")
        self.assertNotEqual(h1, h2)

if __name__ == '__main__':
    unittest.main()