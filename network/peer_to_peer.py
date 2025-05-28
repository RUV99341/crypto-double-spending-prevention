import socket
import threading
import json
import time
import pickle
import base64
from blockchain.transaction import Transaction
from blockchain.block import Block

class PeerToPeer:
    def __init__(self, host='127.0.0.1', port=5000, blockchain=None):
        """
        Initialize the peer-to-peer networking component.
        
        Args:
            host: Host IP address (default: localhost)
            port: Port to listen on (default: 5000)
            blockchain: Reference to the blockchain
        """
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers = set()  # Set of (host, port) tuples
        self.server_socket = None
        self.is_listening = False
        self.listener_thread = None
    
    def start_server(self):
        """Start the server to listen for incoming connections."""
        if self.is_listening:
            print("Server is already running")
            return False
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            
            self.is_listening = True
            self.listener_thread = threading.Thread(target=self._listen_for_connections)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            print(f"P2P server started on {self.host}:{self.port}")
            return True
        
        except Exception as e:
            print(f"Failed to start P2P server: {e}")
            return False
    
    def stop_server(self):
        """Stop the server."""
        self.is_listening = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        if self.listener_thread:
            self.listener_thread.join(timeout=1)
            self.listener_thread = None
        
        print("P2P server stopped")
    
    def _listen_for_connections(self):
        """Listen for incoming connections in a loop."""
        print("Listening for incoming connections...")
        
        while self.is_listening:
            try:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                print(f"New connection from {address[0]}:{address[1]}")
            
            except OSError:
                if self.is_listening:
                    print("Error accepting connection")
            except Exception as e:
                print(f"Error in listener: {e}")
    
    def _handle_client_connection(self, client_socket, address):
        """
        Handle communication with a connected client.
        
        Args:
            client_socket: Socket connected to the client
            address: Address of the client
        """
        try:
            # Set a timeout for receiving data
            client_socket.settimeout(60)  # 60 seconds
            
            # Receive message
            data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we've received the full message
                if len(chunk) < 4096:
                    break
            
            if not data:
                print(f"Empty data received from {address}")
                return
            
            # Process the message
            message = pickle.loads(data)
            self._process_message(message, address)
            
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        
        finally:
            client_socket.close()
    
    def _process_message(self, message, sender_address):
        """
        Process a received message.
        
        Args:
            message: The received message dictionary
            sender_address: Address of the sender
        """
        message_type = message.get('type')
        data = message.get('data')
        
        if not message_type or not data:
            print("Invalid message format")
            return
        
        print(f"Received {message_type} message from {sender_address}")
        
        if message_type == 'TRANSACTION':
            # Process new transaction
            transaction_dict = data
            transaction = Transaction(
                sender=transaction_dict['sender'],
                receiver=transaction_dict['receiver'],
                amount=transaction_dict['amount'],
                timestamp=transaction_dict['timestamp'],
                signature=transaction_dict['signature'],
                tx_id=transaction_dict['tx_id']
            )
            
            if self.blockchain:
                # Add transaction to blockchain's unconfirmed transactions
                if self.blockchain.add_transaction(transaction):
                    print(f"Added transaction {transaction.tx_id} to pool")
                else:
                    print(f"Failed to add transaction {transaction.tx_id}")
        
        elif message_type == 'BLOCK':
            # Process new block
            block_dict = data
            
            # Create transactions from dict
            transactions = []
            for tx_dict in block_dict['transactions']:
                tx = Transaction(
                    sender=tx_dict['sender'],
                    receiver=tx_dict['receiver'],
                    amount=tx_dict['amount'],
                    timestamp=tx_dict['timestamp'],
                    signature=tx_dict['signature'],
                    tx_id=tx_dict['tx_id']
                )
                transactions.append(tx)
            
            # Create block from dict
            block = Block(
                index=block_dict['index'],
                previous_hash=block_dict['previous_hash'],
                transactions=transactions,
                timestamp=block_dict['timestamp'],
                nonce=block_dict['nonce']
            )
            block.hash = block_dict['hash']
            block.merkle_root = block_dict['merkle_root']
            
            # TODO: Validate and add block to blockchain
            # This would require additional blockchain functionality
            print(f"Received block {block.index} with hash {block.hash[:10]}...")
        
        elif message_type == 'PEER':
            # Add new peer
            peer_host = data['host']
            peer_port = data['port']
            self.add_peer(peer_host, peer_port)
            
            # Send our peer list back
            self.broadcast_peer_list([(peer_host, peer_port)])
        
        elif message_type == 'PEER_LIST':
            # Update peer list
            for peer in data:
                self.add_peer(peer[0], peer[1])
        
        elif message_type == 'SYNC_REQUEST':
            # Send our blockchain to the requester
            self.send_blockchain(sender_address[0], data['port'])
        
        elif message_type == 'BLOCKCHAIN':
            # Process received blockchain
            # This would require validation and potentially chain replacement
            print("Received blockchain data")
        
        else:
            print(f"Unknown message type: {message_type}")
    
    def add_peer(self, host, port):
        """
        Add a peer to the network.
        
        Args:
            host: Peer host address
            port: Peer port
            
        Returns:
            bool: True if peer was added, False if already known
        """
        # Don't add ourselves
        if host == self.host and port == self.port:
            return False
        
        peer = (host, port)
        if peer not in self.peers:
            self.peers.add(peer)
            print(f"Added peer: {host}:{port}")
            return True
        
        return False
    
    def connect_peer(self, host, port):
        """
        Connect to a new peer and exchange information.
        
        Args:
            host: Peer host address
            port: Peer port
            
        Returns:
            bool: True if connection was successful
        """
        # Add to our peer list
        self.add_peer(host, port)
        
        # Send our info to the peer
        message = {
            'type': 'PEER',
            'data': {
                'host': self.host,
                'port': self.port
            }
        }
        
        try:
            self._send_to_peer(host, port, message)
            print(f"Connected to peer {host}:{port}")
            return True
        
        except Exception as e:
            print(f"Failed to connect to peer {host}:{port}: {e}")
            return False
    
    def broadcast_transaction(self, transaction):
        """
        Broadcast a transaction to all known peers.
        
        Args:
            transaction: Transaction object to broadcast
            
        Returns:
            int: Number of peers the transaction was sent to
        """
        # Prepare message
        message = {
            'type': 'TRANSACTION',
            'data': transaction.to_dict()
        }
        
        # Broadcast to all peers
        return self._broadcast_message(message)
    
    def broadcast_block(self, block):
        """
        Broadcast a block to all known peers.
        
        Args:
            block: Block object to broadcast
            
        Returns:
            int: Number of peers the block was sent to
        """
        # Prepare message
        message = {
            'type': 'BLOCK',
            'data': block.to_dict()
        }
        
        # Broadcast to all peers
        return self._broadcast_message(message)
    
    def broadcast_peer_list(self, peers_to_send=None):
        """
        Broadcast our peer list to all or specified peers.
        
        Args:
            peers_to_send: List of peers to send to (if None, send to all)
            
        Returns:
            int: Number of peers the list was sent to
        """
        # Prepare message with peer list
        message = {
            'type': 'PEER_LIST',
            'data': list(self.peers)
        }
        
        # Broadcast to specified peers or all peers
        if peers_to_send:
            sent_count = 0
            for peer in peers_to_send:
                try:
                    self._send_to_peer(peer[0], peer[1], message)
                    sent_count += 1
                except Exception as e:
                    print(f"Failed to send peer list to {peer}: {e}")
            return sent_count
        else:
            return self._broadcast_message(message)
    
    def sync_chain(self, host, port):
        """
        Request blockchain sync from a specific peer.
        
        Args:
            host: Peer host address
            port: Peer port
            
        Returns:
            bool: True if request was sent successfully
        """
        message = {
            'type': 'SYNC_REQUEST',
            'data': {
                'port': self.port
            }
        }
        
        try:
            self._send_to_peer(host, port, message)
            return True
        except Exception as e:
            print(f"Failed to request chain sync from {host}:{port}: {e}")
            return False
    
    def send_blockchain(self, host, port):
        """
        Send our blockchain to a peer.
        
        Args:
            host: Peer host address
            port: Peer port
            
        Returns:
            bool: True if blockchain was sent successfully
        """
        if not self.blockchain:
            print("No blockchain to send")
            return False
        
        # Prepare blockchain data
        chain_data = []
        for block in self.blockchain.chain:
            chain_data.append(block.to_dict())
        
        message = {
            'type': 'BLOCKCHAIN',
            'data': chain_data
        }
        
        try:
            self._send_to_peer(host, port, message)
            return True
        except Exception as e:
            print(f"Failed to send blockchain to {host}:{port}: {e}")
            return False
    
    def _send_to_peer(self, host, port, message):
        """
        Send a message to a specific peer.
        
        Args:
            host: Peer host address
            port: Peer port
            message: Message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Create socket and connect to peer
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)  # 10 seconds timeout
                s.connect((host, port))
                
                # Serialize and send message
                data = pickle.dumps(message)
                s.sendall(data)
                
                return True
        
        except Exception as e:
            print(f"Error sending to {host}:{port}: {e}")
            # Remove failed peer from list
            self.peers.discard((host, port))
            raise
    
    def _broadcast_message(self, message):
        """
        Broadcast a message to all known peers.
        
        Args:
            message: Message to broadcast
            
        Returns:
            int: Number of peers the message was sent to
        """
        successful_peers = 0
        
        # Make a copy of the peers set to avoid modification during iteration
        peers_copy = self.peers.copy()
        
        for peer in peers_copy:
            try:
                self._send_to_peer(peer[0], peer[1], message)
                successful_peers += 1
            except Exception:
                # Error already logged in _send_to_peer
                pass
        
        return successful_peers
    
    def get_peer_count(self):
        """Get the number of connected peers."""
        return len(self.peers)
    
    def get_peers(self):
        """Get a list of all known peers."""
        return list(self.peers)
    
    def detect_unusual_activity(self):
    # Placeholder: always return False for now
        return False

    
    def __repr__(self):
        """Debug-friendly string representation."""
        status = "running" if self.is_listening else "stopped"
        return f"P2P(address={self.host}:{self.port}, status={status}, peers={len(self.peers)})"
    

# if __name__ == "__main__":
#     p2p = PeerToPeer()
#     p2p.start_server()
#     p2p.send_blockchain('127.0.0.1', 5000)
#     time.sleep(5)
#     print(p2p.get_peers())
#     p2p.stop_server()
