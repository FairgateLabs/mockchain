from mockchain.blockchain import Blockchain, Wallet
from mockchain.bitcoin import Bitcoin
from mockchain.cardano import Cardano
from typing import List, Optional, Callable
import asyncio

class Agent:
    cnt = 0

    def __init__(self, name: Optional[str] = None):
        if name is None:
            name = "agent"+str(Agent.cnt)
            Agent.cnt += 1

        self.name = name
        self.wallet = Wallet(name)

    async def setup(self, scenario):
        pass

    async def run(self, scenario):
        pass

    def listen(self, service, callback):
        self.scenario.listen(self.name, service, callback)

    async def connect(self, host, service):
        return await self.scenario.connect(host, service)
       
    async def send(self, host, service, *message):
        sendmsg = await self.connect(host, service)
        return await sendmsg(*message)
    
def get_url(host, service):
    return f"{host}/{service}"

class Scenario:
    def __init__(self, agents: List[Agent | Callable], blockchains : List[Blockchain] = None):
        if blockchains is None:
            blockchains = [Bitcoin()]

        self.blockchains = blockchains
        self.faucet = blockchains[0].faucet
        self.alice = Wallet('alice')
        self.bob = Wallet('bob') 
        self.carol = Wallet('carol')
        self.agents = agents
        self.block_limit = None
        self.endpoints = {}
       

        for blockchain in self.blockchains:
            self.__setattr__(blockchain.name, blockchain)

       
        for agent in agents:
            if not isinstance(agent, Agent):
                continue

            agent.scenario = self

            for blockchain in self.blockchains:
                agent.__setattr__(blockchain.name, blockchain)
            
                tx = blockchain.transfer(blockchain.faucet, agent.wallet, 10000)
                blockchain.add_transaction(tx)
                blockchain.mine_block()
                
        self.status = "initialized" 

    def listen(self, host: str, service : str, callback : Callable): 
        url = get_url(host, service)
        
        listener = self.endpoints.get(url, None)

        if isinstance(listener, asyncio.Event):
            listener.set()
            listener = None
        
        self.endpoints[url] = callback
  
    async def connect(self, host, service):
        url = get_url(host, service)
        listener = self.endpoints.get(url, None)
        if listener is None:
            listener = asyncio.Event()
            self.endpoints[url] = listener

        if isinstance(listener, asyncio.Event):
            await listener.wait()
            listener = self.endpoints[url]
            
        return listener

    async def send(self, host, service, *message):
        listener = await self.connect(host, service)
        return await listener(*message)  

    async def run_blockchains(self, block_limit: Optional[int] = None):
        while block_limit is None or block_limit > 0:
            await asyncio.sleep(self.block_time)

            for blockchain in self.blockchains:
                blockchain.mine_block()

            if block_limit is not None:
                block_limit -= 1


    async def setup_agents(self):
        setup = [agent.setup(self) for agent in self.agents if isinstance(agent, Agent)]
        if len(setup) > 0:
            await asyncio.gather(*setup)


    async def run_agents(self):
        tasks = [agent.run(self) if isinstance(agent, Agent) else agent(self) for agent in self.agents]
        if len(tasks) > 0:
            await asyncio.gather(*tasks)


    async def run(self, block_time=0.001, block_limit: Optional[int] = None):
        self.block_time = block_time

        blockchains_task = asyncio.create_task(self.run_blockchains(block_limit))
        setup_task = asyncio.create_task(self.setup_agents())

        self.status = "running setup"
        await asyncio.wait([blockchains_task, setup_task], return_when=asyncio.FIRST_COMPLETED)

        for task in [blockchains_task, setup_task]:
            e = task.exception() if task.done() else None
            if e is not None:
                self.status = "exception during setup"
                raise e
            
        if blockchains_task.done():
            setup_task.cancel()
            self.status = "blockchain limit reached during setup"
            return False
        
        self.status = "running agents"

        run_task = asyncio.create_task(self.run_agents())
        complete, incomplete = await asyncio.wait([blockchains_task, run_task], return_when=asyncio.FIRST_COMPLETED)
        
        done_blockchains = blockchains_task.done()
        done_run = run_task.done()

        if len(incomplete) > 0:
            for task in incomplete:
                task.cancel()

            try:
                await asyncio.wait(incomplete, return_when=asyncio.ALL_COMPLETED)
            except asyncio.CancelledError:
                pass   
            

        for task in complete:
            e = task.exception() if task.done() else None
            if e is not None and e is not asyncio.CancelledError:
                
                self.status = "exception during run"
                self.result = False
                raise e


        if done_blockchains:
            self.status = "blockchain limit reached during run"
            self.result = False
            return

        self.result = done_run

        return done_run

    def execute(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.run(*args, **kwargs))
        loop.close()

        return self.result