from mockchain.scenario import Agent, Scenario
from mockchain.bitcoin import Bitcoin
from mockchain.cardano import Cardano, ScriptContext, ScriptPurpose, Value, Output
from mockchain.program import Program

id = "nft"
minting_address = ""

def policy(redeemers, context : ScriptContext):
    """
    This is a policy script for a non-fungible token (NFT).
    globals:
        all_address"""
    
    if context.purpose != ScriptPurpose.Minting:
        return False
    
    tx = context.txinfo
    mint = tx.mint[context.policy] 

    minting = False
    for token in mint:
        if token.startswith("-"):
            if mint[token] == 1:
                # Minting InitBurn token. Origianl Token should be -1
                original_token = token[1:]
                if original_token not in mint or mint[original_token] != -1:
                    return False
        else:
            if mint[token] == 1:
                minting = True

    print(minting_address, tx.signatories)

    if minting and minting_address not in tx.signatories:
        return False
    
    return True


class Agent0(Agent):
    async def setup(self, scenario):
        alice=scenario.alice
        bob=scenario.bob
        self.policy1 = Program.address(policy, minting_address=alice.address)
        self.policy2 = Program.address(policy, minting_address=bob.address)

    async def run(self, scenario):
        tx0 = self.cardano.create_mint_transaction(Value.Token(self.policy1, "NFT1", 1), scenario.carol)
        tx0.sign(scenario.alice)

        tx1 = self.cardano.create_mint_transaction(Value.Token(self.policy2, "NFT2", 1), scenario.carol)
        tx1.sign(scenario.bob)

        tx2 = self.cardano.create_mint_transaction(Value.Token(self.policy1, "NFT3", 1), scenario.carol)
        tx2.sign(scenario.bob)

        tx3 = self.cardano.create_mint_transaction(Value.Token(self.policy2, "NFT4", 1), scenario.carol)
        tx3.sign(scenario.alice)


        


        self.cardano.add_transaction(tx0)
        self.cardano.add_transaction(tx1)
        self.cardano.add_transaction(tx2)
        self.cardano.add_transaction(tx3)

        txs = [tx0, tx1, tx2, tx3]
        for tx in txs:
            await self.cardano.wait_for_transaction(tx)
            print(tx)
            

        burn1 = Value.Token(self.policy1, "-NFT1", 1)+Value.Token(self.policy1, "NFT1", -1)
        burn2 = Value.Token(self.policy2, "-NFT2", 1)+Value.Token(self.policy2, "NFT1", -1)
        
        # tx5: burn init. Will work -NFT1 +1 and NFT1 -1
        # tx6: burn init. Will fail -NFT2 +1 and NFT1 -1
        tx5 = self.cardano.create_transaction([tx0.outputs[0].ptr], [Output(scenario.carol, Value.Token(self.policy1, "-NFT1", 1))], mint=burn1)
        tx6 = self.cardano.create_transaction([tx1.outputs[0].ptr], [Output(scenario.carol, Value.Token(self.policy2, "-NFT2", 1))], mint=burn2)   

        for tx in [tx5, tx6]:
            tx.sign(scenario.carol)
            self.cardano.add_transaction(tx)
            await self.cardano.wait_for_transaction(tx)
            print(tx)

        burn3 = Value.Token(self.policy1, "-NFT1", -1)
        # final burn
        tx7 = self.cardano.create_transaction([tx5.outputs[0].ptr], [Output(scenario.carol, Value())], mint=burn3)

        for tx in [tx7]:
            tx.sign(scenario.carol)
            self.cardano.add_transaction(tx)
            await self.cardano.wait_for_transaction(tx)
            print(tx)

        print("done")


scenario = Scenario([Agent0()], [Cardano()])


result = scenario.execute()
scenario.cardano.print_utxos()