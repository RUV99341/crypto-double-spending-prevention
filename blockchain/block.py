import time
import hashlib
import json
# from Crypto.Hash import SHA256

class Block:
    def __init__(self, index, previous_hash, transactions, timestamp=None, nonce=0):
        """
        Initialize a new block in the blockchain.
        
        Args:
            index: Block height in the chain
            previous_hash: Hash of the previous block
            transactions: List of Transaction objects
            timestamp: Time block was created (defaults to current time)
            nonce: Value for Proof-of-Work (defaults to 0)
        """
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp if timestamp else time.time()
        self.nonce = nonce
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """
        Calculate the hash of this block.
        
        Returns:
            str: SHA-256 hash of block data
        """
        block_string = json.dumps(self.to_dict(include_hash=False), sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def calculate_merkle_root(self):
        """
        Calculate the Merkle root of the transactions.
        
        Returns:
            str: Merkle root hash of all transactions
        """
        if not self.transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        tx_hashes = [tx.tx_id for tx in self.transactions]
        
        # If odd number of transactions, duplicate the last one
        if len(tx_hashes) % 2 != 0:
            tx_hashes.append(tx_hashes[-1])
        
        # Bottom-up construction of Merkle tree
        while len(tx_hashes) > 1:
            new_tx_hashes = []
            
            # Process pairs of hashes
            for i in range(0, len(tx_hashes), 2):
                # Concatenate pair of hashes and hash them
                concat_hash = tx_hashes[i] + tx_hashes[i+1]
                new_hash = hashlib.sha256(concat_hash.encode()).hexdigest()
                new_tx_hashes.append(new_hash)
            
            tx_hashes = new_tx_hashes
            
            # If odd number of hashes, duplicate the last one
            if len(tx_hashes) % 2 != 0 and len(tx_hashes) > 1:
                tx_hashes.append(tx_hashes[-1])
        
        return tx_hashes[0] if tx_hashes else ""
    
    def to_dict(self, include_hash=True):
        """
        Convert block to dictionary format.
        
        Args:
            include_hash: Whether to include block hash in the dictionary
            
        Returns:
            dict: Dictionary representation of the block
        """
        block_dict = {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'merkle_root': self.merkle_root
        }
        
        if include_hash:
            block_dict['hash'] = self.hash
            
        return block_dict
    
    def to_json(self):
        """Convert block to JSON format."""
        return json.dumps(self.to_dict(), sort_keys=True)
    
    def __repr__(self):
        """Debug-friendly string representation."""
        return (f"Block(index={self.index}, "
                f"hash={self.hash[:10]}..., "
                f"prev_hash={self.previous_hash[:10]}..., "
                f"tx_count={len(self.transactions)}, "
                f"nonce={self.nonce})")
    


# block.py (at the bottom of the file)

if __name__ == "__main__":
    from .transaction import Transaction  # make sure this path is correct

    # Create a couple of dummy transactions
    tx1 = Transaction("Alice", "Bob", 5)
    tx2 = Transaction("Bob", "Charlie", 2)
    
    # (Optionally sign them if you have keys; here we just use IDs)
    
    # Create the block with those transactions
    block = Block(index=1,
                  previous_hash="0"*64,
                  transactions=[tx1, tx2])
    
    # Print out the block’s repr, its merkle root, and its hash
    print(block)
    print("Merkle Root:", block.merkle_root)
    print("Block Hash: ", block.hash)
