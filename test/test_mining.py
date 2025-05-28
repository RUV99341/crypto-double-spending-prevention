import time
from threading import Thread

# Fake Transaction class for testing
class Transaction:
    def __init__(self, sender, amount):
        self.sender = sender
        self.amount = amount
        self.tx_id = "tx123"

# Fake Blockchain class with minimal interface Miner needs
class FakeBlockchain:
    def __init__(self):
        self.unconfirmed_transactions = [
            Transaction("Alice", 5),
            Transaction("Bob", 10),
            Transaction("0", 50)  # Mining reward tx (sender = "0")
        ]
    
    def get_balance(self, sender):
        # For simplicity, just give some fixed balances
        if sender == "Alice":
            return 10
        elif sender == "Bob":
            return 5
        else:
            return 100

    def mine_block(self, miner_id):
        # Simulate mining a block (normally more complex)
        print(f"Mining block rewarded to miner: {miner_id}")
        # Clear transactions to simulate they're included in the block
        self.unconfirmed_transactions.clear()
        return "block123"  # fake block identifier

# Paste your Miner class here or import it if in another file
# from mining.miner import Miner  # Adjust import as needed

# Using your Miner class code (just ensure it's defined here or imported)

def test_miner():
    blockchain = FakeBlockchain()
    miner = Miner(miner_id="Miner1", blockchain=blockchain)

    print(miner)
    miner.start_mining()

    # Let it mine for a few seconds, then stop
    time.sleep(5)
    miner.stop_mining()
    print(miner)

if __name__ == "__main__":
    test_miner()
