# Mockchain README

Mockchain is a simple Python library that provides a basic implementation of bitcoins. It allows developers to illustrate ideas by showing how different components will interact.

## Features
- Simulate bitcoin and cardano bitcoins
- manage public key cryptography, key aggregation and transfer of ownership protocols
- Has support for scenarios with simple agent systems
- manage a vm for disputable computing

## Installation

- Create a virtualenv
- Run `pip install -r requirements.txt`

## Usage
Here is a simple example of how to use the MockChain library:

```python
from mockchain import Bitcoin, Wallet

# Create a new instance of MockChain
bitcoin = Bitcoin()
alice = Wallet('alice')
faucet = bitcoin.faucet
tx = bitcoin.transfer(faucet, alice, 100)
bitcoin.add_transaction(tx)
bitcoin.mine_block()
bitcoin.print()
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.