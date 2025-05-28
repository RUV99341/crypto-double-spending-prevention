import time
import json
from .block import Block
from .transaction import Transaction
from mining.proof_of_work import proof_of_work, is_valid_proof
from blockchain.utxo import UTXOSet

class Blockchain:
    def __init__(self, difficulty=4, miner_address=None):
        """
        Initialize a new blockchain.
        
        Args:
            difficulty: Mining difficulty (number of zeros needed in hash prefix)
        """
        self.utxo_set = UTXOSet()
        self.chain = []
        self.unconfirmed_transactions = []
        self.difficulty = difficulty
        self.last_known_hash = None
        # self.utxo_set = {} # Dictionary to track unspent transaction outputs
        if miner_address:
            self.create_genesis_block(miner_address)
    
    # def create_genesis_block(self):
    #     """Create the first block in the chain (genesis block)."""
    #     genesis_block = Block(
    #         index=0,
    #         previous_hash="0" * 64,
    #         transactions=[],
    #         timestamp=time.time()
    #     )
    #     # No mining required for genesis block
    #     self.chain.append(genesis_block)
    #     return genesis_block
    
    def create_genesis_block(self,miner_address):
        reward_tx = Transaction(sender="0", receiver=miner_address, amount=50, timestamp=time.time())
        reward_tx.tx_id = reward_tx._calculate_tx_id()
        reward_tx.signature = "GENESIS"
        genesis_block = Block(index=0, previous_hash="0"*64, transactions=[reward_tx], timestamp=time.time())
        self.chain.append(genesis_block)
        self.utxo_set.update_utxos(reward_tx)
        return genesis_block

    def get_latest_block(self):
        """Get the most recent block in the chain."""
        return self.chain[-1]
    
    def add_transaction(self, transaction):
        """
        Add a transaction to the pool of unconfirmed transactions.
        
        Args:
            transaction: The Transaction object to add
            
        Returns:
            bool: True if transaction is valid and added, False otherwise
        """
        # Verify transaction signature
        if not transaction.verify_signature():
            print(f"Invalid transaction signature: {transaction.tx_id}")
            return False
        
        # Check if sender has enough balance (UTXO)
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance < transaction.amount:
            print(f"Insufficient balance: {transaction.sender} has {sender_balance}, needs {transaction.amount}")
            return False
        
        # Add to unconfirmed transactions pool
        self.unconfirmed_transactions.append(transaction)
        return True
    
    def mine_block(self, miner_address):
        """
        Mine a new block with unconfirmed transactions.
        
        Args:
            miner_address: Address of the miner (for block reward)
            
        Returns:
            Block or None: The mined block if successful, None otherwise
        """
        if not self.unconfirmed_transactions:
            return None
        
        # Create mining reward transaction
        reward_tx = Transaction(
            sender="0",  # "0" signifies system/mining reward
            receiver=miner_address,
            amount=5.0,  # Block reward of 5 coins
            timestamp=time.time()
        )
       
        reward_tx.signature = "COINBASE"
        reward_tx.tx_id = reward_tx._calculate_tx_id()
        # Add reward to beginning of block transactions
       

        block_transactions = [reward_tx] + self.unconfirmed_transactions[:10]  # Limit of 10 transactions per block
        
        last_block = self.get_latest_block()
        new_block = Block(
            index=last_block.index + 1,
            previous_hash=last_block.hash,
            transactions=block_transactions
        )
        
        # Apply proof of work
        proof_result = proof_of_work(new_block, self.difficulty)
        if not proof_result:
            return None
        
        # If mining successful, update the block with proof of work result
        new_block.nonce = proof_result['nonce']
        new_block.hash = proof_result['hash']
        
        # Add block to chain
        self.chain.append(new_block)
        self.last_known_hash = new_block.hash
        # Update UTXO set with the processed transactions
        for tx in block_transactions:
            result = self.utxo_set.update_utxos(tx)
            print(f"🔄 update_utxos(tx_id={tx.tx_id}) => {result}")

        # Remove processed transactions from unconfirmed pool
        for tx in block_transactions[1:]:  # Skip the reward transaction
            if tx in self.unconfirmed_transactions:
                self.unconfirmed_transactions.remove(tx)
        # only for checking purposes
        

        return new_block
    
    
    def get_balance(self, address):
        """
        Calculate the balance of a wallet address from the UTXO set.
        
        Args:
            address: The wallet address to check
            
        Returns:
            float: The balance of the address
        """
        return self.utxo_set.get_balance(address)

        # if address not in self.utxo_set:
        #     return 0.0
        
        # # Sum up all unspent transaction outputs for this address
        # balance = sum(utxo['amount'] for utxo in self.utxo_set.get(address, []))
        # return balance
    
    def is_chain_valid(self):
        """
        Validate the entire blockchain.
        
        Returns:
            bool: True if the chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if the current block's hash is correct
            if current_block.hash != current_block.calculate_hash():
                print(f"Invalid hash in block {i}")
                return False
            
            # Check if this block points to the previous block's hash
            if current_block.previous_hash != previous_block.hash:
                print(f"Block {i} doesn't link to previous block")
                return False
            
            # Check if the block's proof of work is valid
            if not is_valid_proof(current_block, self.difficulty):
                print(f"Invalid proof of work in block {i}")
                return False
        
        return True
    
    def to_json(self):
        """Convert the blockchain to JSON format."""
        chain_data = []
        for block in self.chain:
            chain_data.append(block.to_dict())
        
        blockchain_dict = {
            'chain': chain_data,
            'length': len(self.chain),
            'difficulty': self.difficulty
        }
        
        return json.dumps(blockchain_dict, sort_keys=True)
    
    # def detect_chain_reorg(self) -> bool:
    def detect_chain_reorg(self) -> bool:
        """
        Detects if the chain tip has changed unexpectedly,
        which may indicate a chain reorganization.
        """
        if not self.chain:
            return False

        current_hash = self.chain[-1].hash

        if self.last_known_hash and current_hash != self.last_known_hash:
        # Chain tip changed unexpectedly
            self.last_known_hash = current_hash  # Update to new tip
            return True

        # No change detected
        self.last_known_hash = current_hash
        return False


    
    def __repr__(self):
        """Debug-friendly string representation."""
        return (f"Blockchain(blocks={len(self.chain)}, "
                f"difficulty={self.difficulty}, "
                f"unconfirmed_tx={len(self.unconfirmed_transactions)})")