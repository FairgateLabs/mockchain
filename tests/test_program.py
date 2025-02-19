import unittest
from mockchain.program import Program

class TestProgram(unittest.TestCase):
    def test_create(self):
        def f1():
            return 1

        def f2():
            return 2

        def f3():
            return 3

      
        h1 = Program.address(f1, x=1)
        h2 = Program.address(f2, x=1)
        h3 = Program.address(f1, x=1)
        
        h4 = Program.address(f1, x=2)

        self.assertNotEqual(h1, h2)
        self.assertEqual(h1, h3)
        self.assertNotEqual(h1, h4)



    def test_call(self):
        def f1():
            return 1

        def f2():
            return x+1

        def f3(a,b):
            return a+b

        h1 = Program.address(f1)
        h2 = Program.address(f2, x=10)
        h3 = Program.address(f2, x=20)
        h4 = Program.address(f3)

        self.assertEqual(h1.program.run(), 1)
        self.assertEqual(h2.program.run(), 11)
        self.assertEqual(h3.program.run(), 21)
        self.assertEqual(h4.program.run(10,20), 30)
        