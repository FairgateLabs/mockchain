import unittest
from asyncio import gather, sleep, Future, Event, run
from mockchain.scenario import Agent, Scenario

async def agent0(scenario):
    bitcoin = scenario.bitcoin

    await bitcoin.wait_for_block(3)
    tx = bitcoin.transfer(bitcoin.faucet, scenario.alice, 1000)
    bitcoin.add_transaction(tx)
    await bitcoin.wait_for_transaction(tx)
    tx2 = bitcoin.transfer(scenario.alice, scenario.bob, 500)
    await bitcoin.wait_for_transaction_hash(tx2.hash)   
    print("mined")
    
class Agent1(Agent):
    async def run(self, scenario):
        bitcoin = scenario.bitcoin
        tx = bitcoin.transfer(bitcoin.faucet, scenario.alice, 1000)
        await bitcoin.wait_for_transaction_hash(tx.hash)
        await bitcoin.wait_for_block(bitcoin.block_height+5)
        tx2 = bitcoin.transfer(scenario.alice, scenario.bob, 500)
        bitcoin.add_transaction(tx2)
        await bitcoin.wait_for_transaction(tx2)



class Agent2(Agent):
    async def setup(self, scenario):
        self.signal = Event()
        scenario.listen("agent2", "ping", self.on_ping)

    async def on_ping(self, message):
        self.signal.set()

    async def run(self, scenario):
        await self.signal.wait()
    
class Agent3(Agent):
    async def run(self, scenario):
        await sleep(0.001)
        await self.send("agent2", "ping", "hello")

class Agent4(Agent):
    async def setup(self, scenario):
        self.signal = Event()
        scenario.listen("agent4", "ping", self.on_ping)

    async def on_ping(self, message):
        self.signal.set()

    async def run(self, scenario):
        await self.signal.wait()
        self.result = await self.send("agent5", "pong", "hello")
        

    
class Agent5(Agent):
    async def run(self, scenario):
        self.signal = Event()
        await self.send("agent4", "ping", "hello")
        await sleep(0.01)
        scenario.listen("agent5", "pong", self.on_pong)
        await self.signal.wait()

    async def on_pong(self, message):
        self.signal.set() 
        return 42

class TestScenario(unittest.IsolatedAsyncioTestCase):
    async def test_blockchains(self):
        scenario = Scenario([agent0, Agent1()])
        result = await scenario.run(block_time=0, block_limit=50)

        self.assertTrue(result)

    async def test_timeout(self):     
        scenario = Scenario([agent0])
        result = await scenario.run(block_limit=50)

        self.assertFalse(result)

class TestEndpoints(unittest.IsolatedAsyncioTestCase):
    async def test_send(self):
        scenario = Scenario([Agent2(), Agent3()])
        result = await scenario.run(block_time=0, block_limit=50)

        self.assertTrue(result)

    async def test_connect(self):
        scenario = Scenario([Agent4(), Agent5()])
        result = await scenario.run(block_time=0, block_limit=None)

        self.assertTrue(result)
        self.assertEqual(scenario.agents[0].result, 42)