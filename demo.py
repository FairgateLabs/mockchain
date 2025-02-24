from mockchain.scenario import Agent, Scenario
from mockchain.bitcoin import Bitcoin
from mockchain.cardano import Cardano

async def agent0(scenario):
    bitcoin = scenario.bitcoin

    await bitcoin.wait_for_block(3)
    tx = bitcoin.transfer(bitcoin.faucet, scenario.alice, 1000)
    bitcoin.add_transaction(tx)
    await bitcoin.wait_for_transaction(tx)
    print("transfered")

class Agent1(Agent):
    async def run(self, scenario):
        await self.bitcoin.wait_for_block(30)
        tx1 = self.bitcoin.transfer(self.wallet, self.scenario.alice, 1000)
        self.bitcoin.add_transaction(tx1)
        await self.bitcoin.wait_for_transaction(tx1)
        tx2 = self.cardano.transfer(self.wallet, self.scenario.bob, 500)
        self.cardano.add_transaction(tx2)
        await self.cardano.wait_for_transaction(tx2)
        print("done")

scenario = Scenario([agent0, Agent1()], [Bitcoin(), Cardano()])

result = scenario.execute()
print(scenario.blockchains[0].block_height, "blocks")

print(result)
