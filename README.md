# mockchain/mockchain/README.md

# MockChain

MockChain is a simple Python library that provides a basic implementation of a blockchain. It allows developers to illustrate ideas by showing how different components will interact.

## Features
- Simulate a UTXO based blockchain, blocks, transactions and scripts
- manage cryptography, hash, signatures
- manage a vm for disputable computing

## Installation


## Usage
Here is a simple example of how to use the MockChain library:

```python
from mockchain import Blockchain, User

# Create a new instance of MockChain
blockchain = Blockhain()
alice = User('alice')
faucet = blockchain.faucet
tx = blockchain.transfer(faucet, alice, 100)
blockchain.add_transaction(tx)
blockchain.mine_block()
print(tx.hash, tx.status, blockchain.utxo)
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.