import time
import threading
import logging
from typing import List, Dict, Any, Optional

from wallet.wallet import Wallet
from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from .peer_to_peer import PeerToPeer
from notifications.alert_system import AlertSystem
from mining.miner import Miner
from mining.proof_of_work import is_valid_proof
# from blockchain.UTXOSet import is_unspent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Node:
    """
    Represents a node in the cryptocurrency network. 
    Each node maintains its own copy of the blockchain, has a wallet,
    and connects to other nodes in the network.
    """

    def __init__(self, node_id: str, ml_model_path: Optional[str] = None):
        """
        Initialize a node with a unique identifier.
        
        Args:
            node_id: Unique identifier for this node
            ml_model_path: Path to the trained ML model for fraud detection
        """
        self.node_id = node_id
        self.logger = logging.getLogger(f"Node-{node_id}")
        self.logger.info(f"Initializing node {node_id}")
        
        # Core components
        self.wallet = Wallet() # debuging purpose
        self.blockchain = Blockchain(miner_address=self.wallet.address)
        # self.wallet = self.wallet = Wallet(blockchain=self.blockchain) # debuging purpose
        self.wallet.blockchain = self.blockchain
        self.network = PeerToPeer(host="127.0.0.1", port=5000, blockchain=self.blockchain)
        self.alert_system = AlertSystem(node_id)
        self.miner = Miner(node_id, self.blockchain)
        
        # Transaction pool
        # self.pending_transactions = []
        
        # Load ML model if path is provided
        self.ml_model = None
        if ml_model_path:
            self._load_ml_model(ml_model_path)
        
        # Node state
        self.is_running = False
        self.is_mining = False

    def _load_ml_model(self, model_path: str) -> None:
        """
        Load the machine learning model for fraud detection.
        
        Args:
            model_path: Path to the saved model
        """
        try:
            # This is a placeholder - actual implementation would depend on the ML library used
            # For example, if using scikit-learn:
            # import joblib
            # self.ml_model = joblib.load(model_path)
            self.logger.info(f"ML model loaded from {model_path}")
            
            # For demonstration purposes, let's assume the model is loaded
            self.ml_model = True
        except Exception as e:
            self.logger.error(f"Failed to load ML model: {e}")
            self.ml_model = None

    def start(self) -> None:
        """Start the node operation"""
        if self.is_running:
            self.logger.warning("Node is already running")
            return
            
        self.is_running = True
        self.logger.info(f"Node {self.node_id} started")
        
        # Start network communication
        self.network.start_server()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitor_activity)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # Register callback for incoming transactions and blocks
        # self.network.register_transaction_callback(self.receive_transaction)
        # self.network.register_block_callback(self.receive_block)

    def stop(self) -> None:
        """Stop the node operation"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.logger.info(f"Node {self.node_id} stopped")
        
        # Stop network communication
        self.network.stop_server()
        
        # Stop mining if active
        if self.is_mining:
            self.miner.stop_mining()
            self.is_mining = False

    def create_transaction(self, receiver: str, amount: float) -> Optional[Transaction]:
        """
        Create a new transaction from this node's wallet.
        
        Args:
            receiver: Address of the receiver
            amount: Amount to transfer
            
        Returns:
            The created transaction if successful, None otherwise
        """
        # Check if user has sufficient balance
        if self.wallet.get_balance() < amount:
            self.logger.warning(f"Insufficient balance for transaction: {amount}")
            return None
            
        # Create and sign transaction
        transaction = Transaction(
            sender=self.wallet.address,
            receiver=receiver,
            amount=amount,
            timestamp=time.time()
        )
        
        # Sign transaction with private key
        transaction.sign_transaction(self.wallet.private_key)
        
        # Add to pending transactions and broadcast
        self.blockchain.unconfirmed_transactions.append(transaction)
        # self.blockchain.add_transaction(transaction=transaction) # change for debuging purposes
        self.network.broadcast_transaction(transaction)
        
        self.logger.info(f"Created and broadcast transaction: {transaction.tx_id}")
        return transaction

    def receive_transaction(self, transaction: Transaction) -> bool:
        """
        Process a transaction received from the network.
        
        Args:
            transaction: The received transaction
            
        Returns:
            True if transaction is valid and accepted, False otherwise
        """
        self.logger.info(f"Received transaction: {transaction.tx_id}")
        
        # Check if transaction is already in pending pool
        for tx in self.blockchain.unconfirmed_transactions:
            if tx.tx_id == transaction.tx_id:
                self.logger.debug(f"Transaction {transaction.tx_id} already in pending pool")
                return False
        
        # Check if transaction is valid
        if not self.validate_and_add_tx(transaction):
            return False
            
        # Add to pending transactions
        self.blockchain.unconfirmed_transactions.append(transaction)
        
        # Analyze transaction for potential fraud
        if self.ml_model:
            self.check_transaction_fraud(transaction)
            
        return True

    def validate_and_add_tx(self, transaction: Transaction) -> bool:
        """
        Validate a transaction and add it to the pool if valid.
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            True if transaction is valid, False otherwise
        """
        # Check signature
        if not transaction.verify_signature():
            self.logger.warning(f"Invalid signature for transaction: {transaction.tx_id}")
            return False
            
        # Check if sender has sufficient balance
        sender_balance = self.blockchain.get_balance(transaction.sender)
        if sender_balance < transaction.amount:
            self.logger.warning(f"Insufficient balance for transaction: {transaction.tx_id}")
            return False
            
        # Check for double spending
        if self.blockchain.is_double_spending(transaction):
            self.logger.warning(f"Double spending detected for transaction: {transaction.tx_id}")
            
            # Generate alert for double spending attempt
            alert_msg = f"Double spending attempt detected for transaction {transaction.tx_id}"
            self.alert_system.send_alert(transaction.sender, alert_msg)
            
            # Broadcast alert to the network
            self.alert_system.broadcast_alert(self.network.peer_list, {
                "type": "double_spending",
                "transaction_id": transaction.tx_id,
                "sender": transaction.sender,
                "timestamp": time.time()
            })
            
            return False
            
        return True

    def receive_block(self, block: Dict[str, Any]) -> bool:
        """
        Process a block received from the network.
        
        Args:
            block: Block data received from network
            
        Returns:
            True if block is valid and added to chain, False otherwise
        """
        self.logger.info(f"Received block with index: {block['index']}")
        
        # Validate block
        if not is_valid_proof(block, self.blockchain.difficulty):
            self.logger.warning(f"Received invalid block: {block['index']}")
            return False
            
        # Add to blockchain
        added = self.blockchain.add_received_block(block)
        if added:
            # Remove confirmed transactions from pending pool
            self._remove_confirmed_transactions(block['transactions'])
            self.logger.info(f"Added block {block['index']} to blockchain")
            return True
        else:
            self.logger.warning(f"Failed to add block {block['index']} to blockchain")
            return False

    def _remove_confirmed_transactions(self, confirmed_txs: List[Dict[str, Any]]) -> None:
        """
        Remove transactions that have been confirmed in a block from pending pool.
        
        Args:
            confirmed_txs: List of confirmed transaction dictionaries
        """
        confirmed_tx_ids = [tx['tx_id'] for tx in confirmed_txs]
        self.blockchain.unconfirmed_transactions = [tx for tx in self.blockchain.unconfirmed_transactions if tx.tx_id not in confirmed_tx_ids]

    def start_mining(self) -> None:
        """Start mining process in a separate thread"""
        if self.is_mining:
            self.logger.warning("Mining is already active")
            return
            
        self.is_mining = True
        
        # Create a thread for mining
        mining_thread = threading.Thread(target=self._mining_process)
        mining_thread.daemon = True
        mining_thread.start()
        
        self.logger.info("Mining process started")

    def stop_mining(self) -> None:
        """Stop the mining process"""
        if not self.is_mining:
            return
            
        self.miner.stop_mining()
        self.is_mining = False
        self.logger.info("Mining process stopped")

    def _mining_process(self) -> None:
        """Mining process that runs in a separate thread"""
        while self.is_mining and self.is_running:
            # Check if there are enough pending transactions
            if len(self.blockchain.unconfirmed_transactions) < 1:
                time.sleep(5)  # Wait for more transactions
                continue
                
            # Select a batch of pending transactions
            tx_batch = self.blockchain.unconfirmed_transactions[:10]  # Limit batch size
            
            # Mine a new block
            block = self.miner.mine(tx_batch)
            
            # If mining was successful, broadcast the block
            if block:
                self.logger.info(f"Successfully mined block: {block.index}")
                self.network.broadcast_block(block.to_dict())
                
                # Remove confirmed transactions from pending pool
                self._remove_confirmed_transactions([tx.to_dict() for tx in tx_batch])

    def check_transaction_fraud(self, transaction: Transaction) -> None:
        """
        Use ML model to check for potential fraud in a transaction.
        
        Args:
            transaction: Transaction to check
        """
        if not self.ml_model:
            return
            
        # Extract features for ML model
        features = self._extract_transaction_features(transaction)
        
        # Make prediction (placeholder - actual implementation depends on ML library)
        # fraud_score = self.ml_model.predict_proba([features])[0][1]  # Probability of fraud
        
        # For demonstration, simulate a fraud detection
        # In a real system, this would use the actual ML model prediction
        fraud_score = 0.0
        
        # If transaction amount is large compared to typical transactions
        if transaction.amount > 1000:  # Example threshold
            fraud_score += 0.3
            
        # If sender has made multiple transactions in a short time
        recent_txs = [tx for tx in self.blockchain.unconfirmed_transactions
                     if tx.sender == transaction.sender and 
                     time.time() - tx.timestamp < 300]  # Last 5 minutes
        if len(recent_txs) > 5:  # Example threshold
            fraud_score += 0.3
            
        # If fraud score is high enough, generate alert
        if fraud_score > 0.5:  # Example threshold
            alert_msg = f"Suspicious transaction detected: {transaction.tx_id}"
            self.alert_system.send_alert(transaction.sender, alert_msg)
            self.alert_system.send_alert(transaction.receiver, alert_msg)
            
            # Log the alert
            self.alert_system.log_alert({
                "type": "potential_fraud",
                "transaction_id": transaction.tx_id,
                "sender": transaction.sender,
                "receiver": transaction.receiver,
                "amount": transaction.amount,
                "fraud_score": fraud_score,
                "timestamp": time.time()
            })

    def _extract_transaction_features(self, transaction: Transaction) -> List[float]:
        """
        Extract features from a transaction for ML model input.
        
        Args:
            transaction: The transaction to extract features from
            
        Returns:
            List of feature values
        """
        # This is a simplified example - in a real system, 
        # you would extract many more features from the transaction and blockchain state
        
        # Example features:
        # 1. Transaction amount
        # 2. Sender's balance
        # 3. Number of recent transactions by sender
        # 4. Average transaction amount of sender
        # 5. Time since last transaction by sender
        
        sender_balance = self.blockchain.get_balance(transaction.sender)
        
        # Count recent transactions by sender (last hour)
        recent_txs = [tx for tx in self.blockchain.unconfirmed_transactions 
                     if tx.sender == transaction.sender and 
                     time.time() - tx.timestamp < 3600]
        
        # Calculate average transaction amount if possible
        avg_amount = 0
        if recent_txs:
            avg_amount = sum(tx.amount for tx in recent_txs) / len(recent_txs)
            
        # Time since last transaction (seconds)
        time_since_last = 3600  # Default: 1 hour
        if recent_txs:
            last_tx_time = max(tx.timestamp for tx in recent_txs)
            time_since_last = time.time() - last_tx_time
            
        return [
            transaction.amount,
            sender_balance,
            len(recent_txs),
            avg_amount,
            time_since_last
        ]

    def connect_to_peer(self, host: str, port: int) -> bool:
        """
        Connect to another node in the network.
        
        Args:
            peer_address: Address of the peer to connect to
            
        Returns:
            True if connection was successful, False otherwise
        """
        success = self.network.connect_peer(host=host,port=port)
        if success:
            self.logger.info(f"Connected to peer: {host}:{port}")
            # Sync blockchain with new peer
            self.network.sync_chain(host=host, port=port)
        else:
            self.logger.warning(f"Failed to connect to peer: {host}:{port}")
        return success

    def get_node_info(self) -> Dict[str, Any]:
        """
        Get information about this node's state.
        
        Returns:
            Dictionary with node information
        """
        return {
            "node_id": self.node_id,
            "wallet_address": self.wallet.address,
            "balance": self.wallet.get_balance(),
            "blockchain_length": len(self.blockchain.chain),
            "pending_transactions": len(self.blockchain.unconfirmed_transactions),
            "connected_peers": len(self.network.peer_list),
            "is_mining": self.is_mining
        }

    def monitor_activity(self) -> None:
        """
        Continuously monitor blockchain and network activity for anomalies.
        Runs in a separate thread.
        """
        self.logger.info("Starting activity monitoring")
        
        while self.is_running:
            try:
                # Check for chain reorganizations
                if self.blockchain.detect_chain_reorg():
                    self.logger.warning("Chain reorganization detected")
                    # Notify about potential attack
                    self.alert_system.send_alert(
                        self.node_id, 
                        "Blockchain reorganization detected - potential 51% attack"
                    )
                
                # Check for unusually high transaction volume
                tx_count = len(self.blockchain.unconfirmed_transactions)
                if tx_count > 100:  # Example threshold
                    self.logger.warning(f"High transaction volume detected: {tx_count}")
                    self.alert_system.send_alert(
                        self.node_id,
                        f"Unusually high transaction volume detected: {tx_count} pending transactions"
                    )
                
                # Monitor for unusual network behavior
                if self.network.detect_unusual_activity():
                    self.logger.warning("Unusual network activity detected")
                    self.alert_system.send_alert(
                        self.node_id,
                        "Unusual network activity detected - potential DDoS attack"
                    )
                    
                # Sleep before next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in activity monitoring: {e}")
                time.sleep(60)  # Wait before retrying

    def run_node(self) -> None:
        """Main method to run the node"""
        try:
            # Start node operations
            self.start()
            
            # Main loop
            while self.is_running:
                # This would be replaced with actual user interaction in a real application
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down")
            self.stop()
        except Exception as e:
            self.logger.error(f"Error in node operation: {e}")
            self.stop()
            raise
    


# # Example usage if this file is run directly
# if __name__ == "__main__":
#     # Create and start a node
#     node = Node("node1")
#     node.start()
    
#     # Connect to another node (would need to be running already)
#     node.connect_to_peer("localhost", 5000)
    
#     # Create a transaction
#     node.create_transaction("recipient_address", 10.0)
    
#     # Start mining
#     node.start_mining()
    
#     try:
#         # Keep the node running
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         # Stop the node gracefully
#         node.stop()

# import time
# from network.node import Node
def run_end_to_end_test():
    print("\n🚀 Starting end-to-end blockchain backend test...")

    # Initialize node
    node = Node(node_id="test_node")
    node.start()
    time.sleep(2)  # Allow network & mining thread to start

    miner_address = node.wallet.address
    print(f"🔑 Miner wallet address: {miner_address}")

    # Step 1: Mine a block to earn initial balance
    print("\n⛏️  Mining first block for reward...")
    node.blockchain.mine_block(miner_address)
    time.sleep(1)

    print(f"💰 Balance after 1st block: {node.wallet.get_balance()}")

    # Step 2: Create and send a transaction to "recipient123"
    recipient = "recipient123"
    amount = 3.0
    print(f"\n💸 Creating transaction: {miner_address} ➡ {recipient} ({amount})")
    success = node.create_transaction(recipient, amount)
    print("✅ Transaction created" if success else "❌ Transaction failed")

    # Step 3: Mine a second block to confirm transaction
    print("\n⛏️  Mining second block...")
    node.blockchain.mine_block(miner_address)
    time.sleep(1)

    # Step 4: Check balances
    sender_balance = node.wallet.get_balance()
    recipient_balance = node.blockchain.get_balance(recipient)
    print(f"\n📊 Final Balances:")
    print(f"Sender ({miner_address}): {sender_balance}")
    print(f"Receiver ({recipient}): {recipient_balance}")

    # Step 5: Attempt a double spend
    print("\n🔒 Attempting double spend (should fail)...")
    result = node.create_transaction(recipient, sender_balance + 1)  # More than balance
    print("❌ Double spend rejected as expected" if not result else "⚠️ Double spend accepted (bug)")

    # Step 6: Print UTXO state
    print("\n📦 Final UTXO Set:")
    print(node.blockchain.utxo_set)
    for addr in node.blockchain.utxo_set.utxos:
        print(f"   🔎 {addr} →", node.blockchain.utxo_set.get_balance(addr))

    print("\n Blockcahin: ")
    for block in node.blockchain.chain:
        print(block.to_json())

    print("\n✅ End-to-end test completed.\n")


if __name__ == "__main__":
    run_end_to_end_test()
