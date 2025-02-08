import unittest
from mockchain.crypto import hash

class TestCrypto(unittest.TestCase):
    def test_hash(self):
        self.assertEqual(hash("test"), "9f86d081884c7d659a2f")
        
if __name__ == '__main__':
    unittest.main()