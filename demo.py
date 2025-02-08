from mockchain import *

# initialize simulated blockchain
blockchain = Blockchain()
faucet = blockchain.faucet
alice = User('alice')
miner = User('miner')

tx = blockchain.transfer(faucet, alice, 1000)
output = tx.outputs[0]

blockchain.mine_transaction(tx)
print(blockchain.utxo_set)
blockchain.mine_blocks()

# transfer into a p2reveal script (requires a secret to spend)
output2 = Output(500, Script.p2pubkey(alice))
output3 = Output(500, Script.p2reveal([commit("secret")], alice))
tx = blockchain.create_transaction([output.ptr], [output2, output3])
tx.inputs[0].set_witness([alice.sign(tx.hash)])

blockchain.add_transaction(tx)
print(blockchain.utxo_set)
blockchain.mine_blocks()
print(blockchain.utxo_set)


# spend from p2reveal showing signature and "secret"
# this has a 10 block timelock
input = Input(output3.ptr)
output = Output(500, Script.p2timelock(10, alice))
tx = blockchain.create_transaction([input], [output])
tx.inputs[0].set_witness([alice.sign(tx.hash), "secret"])

blockchain.add_transaction(tx)
blockchain.mine_blocks()
print(blockchain.utxo_set)

input=Input(output.ptr)
output=Output(499, Script.p2pubkey(alice))
tx = blockchain.create_transaction([input], [output])
tx.inputs[0].set_witness([alice.sign(tx.hash)])

blockchain.add_transaction(tx)
blockchain.mine_blocks()
print(tx.status)

blockchain.mine_blocks(10)

blockchain.add_transaction(tx)
blockchain.mine_blocks(miner=miner)
print(tx.status)

print(blockchain.utxo_set)

