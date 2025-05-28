import time
import hashlib
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

class Transaction:
    def __init__(self, sender, receiver, amount, timestamp=None, signature=None, tx_id=None):
        """
        Initialize a new transaction.
        
        Args:
            sender: Public key or address of the sender
            receiver: Public key or address of the receiver
            amount: Amount of cryptocurrency to transfer
            timestamp: Time of transaction (defaults to current time)
            signature: Digital signature for authentication (optional)
            tx_id: Unique transaction identifier (optional)
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp if timestamp else time.time()
        self.signature = signature
        self.tx_id = tx_id if tx_id else self._calculate_tx_id()
    
    def _calculate_tx_id(self):
        """Calculate a unique transaction ID based on transaction data."""
        tx_contents = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"
        return hashlib.sha256(tx_contents.encode()).hexdigest()
    
    def to_dict(self):
        """Return a dictionary representation of the transaction."""
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'tx_id': self.tx_id,
            'signature': self.signature
        }
    
    def to_json(self):
        """Convert transaction to JSON format."""
        return json.dumps(self.to_dict(), sort_keys=True)
    
    def transaction_data(self):
        """Return the transaction data that needs to be signed."""
        return json.dumps({
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'tx_id': self.tx_id
        }, sort_keys=True).encode()
    
    def sign_transaction(self, private_key):
        """
        Sign the transaction with the sender's private key.
        
        Args:
            private_key: The private key of the sender
            
        Returns:
            bool: True if signing was successful
        """
        if not self.sender:
            raise ValueError("Cannot sign transactions with no sender")
        
        # Sign the transaction data with the private key
        signature = private_key.sign(
            self.transaction_data(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        self.signature = signature.hex()
        return True
    
    def verify_signature(self, public_key):
        """
        Verify the signature of this transaction using the sender's public key.
        
        Args:
            public_key: The public key object of the sender
            
        Returns:
            bool: True if the signature is valid
        """
        if not self.signature:
            return False
        
        try:
            # Convert hex signature back to bytes
            signature_bytes = bytes.fromhex(self.signature)
            
            # Verify the signature
            public_key.verify(
                signature_bytes,
                self.transaction_data(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def __repr__(self):
        """Debug-friendly string representation."""
        return (f"Transaction(tx_id={self.tx_id}, "
                f"sender={self.sender[:10]}..., "
                f"receiver={self.receiver[:10]}..., "
                f"amount={self.amount}, "
                f"signed={'Yes' if self.signature else 'No'})")



# if __name__ == "__main__":
#     tx = Transaction("Alice", "Bob", 10)
#     transaction_data = tx.transaction_data()
#     print("Transaction Data:", transaction_data)
#     print(tx)
