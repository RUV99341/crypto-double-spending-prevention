# from mining.proof_of_work import ProofOfWork

import time
import threading
from blockchain.blockchain import Blockchain
from .proof_of_work import proof_of_work
from notifications.alert_system import AlertSystem
from blockchain.utxo import UTXOSet
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Miner:
    def __init__(self, miner_id, blockchain, alert_system=None):
        """
        Initialize a miner for cryptocurrency.
        
        Args:
            miner_id: Unique identifier for this miner (wallet address)
            blockchain: Reference to the blockchain
            alert_system: Reference to the alert system (optional)
        """
        self.miner_id = miner_id
        self.blockchain = blockchain
        self.alert_system = alert_system
        self.is_mining = False
        self.mining_thread = None
        
    def start_mining(self):
        """Start the mining process in a separate thread."""
        if self.is_mining:
            print(f"Miner {self.miner_id} is already mining.")
            return
        
        self.is_mining = True
        self.mining_thread = threading.Thread(target=self._mine_continuously)
        self.mining_thread.daemon = True
        self.mining_thread.start()
        print(f"Miner {self.miner_id} started mining.")
    
    def stop_mining(self):
        """Stop the mining process."""
        self.is_mining = False
        if self.mining_thread:
            self.mining_thread.join(timeout=1)
            print(f"Miner {self.miner_id} stopped mining.")
    
    def _mine_continuously(self):
        """Continuously mine blocks until stopped."""
        while self.is_mining:
            if len(self.blockchain.unconfirmed_transactions) > 0:
                # Validate transactions before mining
                valid_txs = self.validate_transactions()
                
                if valid_txs:
                    # Mine a new block
                    print(f"Miner {self.miner_id} mining block with {len(valid_txs)} transactions...")
                    new_block = self.mine()
                    
                    if new_block:
                        print(f"Miner {self.miner_id} successfully mined block {new_block.index}!")
                        # Optional: Could broadcast the block here
                    else:
                        print(f"Miner {self.miner_id} failed to mine block.")
                else:
                    print(f"Miner {self.miner_id} found no valid transactions to mine.")
            else:
                # No transactions to mine, wait a bit
                time.sleep(2)
    
    def mine(self):
        """
        Mine a single block.
        
        Returns:
            Block or None: The mined block if successful, None otherwise
        """
        # Use the blockchain's mining method
        return self.blockchain.mine_block(self.miner_id)
    
    def validate_transactions(self):
        """
        Validate all unconfirmed transactions to ensure they're not double-spending.
        
        Returns:
            list: List of valid transactions
        """
        valid_transactions = []
        suspicious_transactions = []
        
        # Make a copy of unconfirmed transactions to avoid modification during iteration
        transactions_to_validate = self.blockchain.unconfirmed_transactions.copy()
        
        # Track addresses and amounts to detect double-spend attempts
        spending_tracker = {}
        
        for tx in transactions_to_validate:
            # Skip mining rewards
            if tx.sender == "0":
                valid_transactions.append(tx)
                continue
            
            # Get sender's balance
            sender_balance = self.blockchain.get_balance(tx.sender)
            
            # Track spending by this sender in this batch
            if tx.sender in spending_tracker:
                spending_tracker[tx.sender] += tx.amount
            else:
                spending_tracker[tx.sender] = tx.amount
            
            # Check if this transaction would cause overspending
            if spending_tracker[tx.sender] > sender_balance:
                print(f"Potential double-spend detected for {tx.sender}")
                suspicious_transactions.append(tx)
                
                # Alert if alert system is available
                if self.alert_system:
                    self.alert_system.send_alert(
                        "DOUBLE_SPEND",
                        f"Potential double-spend detected for {tx.sender}",
                        {"tx_id": tx.tx_id, "sender": tx.sender, "amount": tx.amount}
                    )
            else:
                valid_transactions.append(tx)
        
        return valid_transactions
    
    def __repr__(self):
        """Debug-friendly string representation."""
        status = "mining" if self.is_mining else "idle"
        return f"Miner(id={self.miner_id}, status={status})"
    


