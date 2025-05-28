import os
import json
import time
import hashlib
import base64
from .key import generate_key_pair, save_key_to_file, load_key_from_file, serialize_public_key
from cryptography.hazmat.primitives.asymmetric import rsa

class Wallet:
    def __init__(self, private_key=None, public_key=None, address=None, blockchain=None):
        """
        Initialize a new wallet for cryptocurrency.
        """
        self.private_key = private_key
        self.public_key = public_key
        self.address = address
        self.blockchain = blockchain

        if not self.private_key or not self.public_key:
            self._generate_keys()

    def _generate_keys(self):
        """Generate a new RSA key pair and address."""
        self.private_key, self.public_key = generate_key_pair()
        self._generate_address()

    def _generate_address(self):
        """Create a wallet address by hashing the public key."""
        pubkey_pem = serialize_public_key(self.public_key).encode()
        sha256_hash = hashlib.sha256(pubkey_pem).digest()
        ripemd_hash = hashlib.sha256(sha256_hash).digest()  # Simplified (instead of RIPEMD-160)
        address = base64.b64encode(ripemd_hash).decode('utf-8')
        self.address = "CRY" + address[:34]

    def save_wallet(self, folder_path=".", password=None):
        """Save keys and wallet info to files."""
        os.makedirs(folder_path, exist_ok=True)

        # Save keys using key.py
        priv_key_file = os.path.join(folder_path, f"wallet_{self.address[:10]}.pem")
        pub_key_file = os.path.join(folder_path, f"wallet_{self.address[:10]}.pub")

        save_key_to_file(self.private_key, priv_key_file, is_private=True, password=password)
        save_key_to_file(self.public_key, pub_key_file, is_private=False)

        # Save wallet info
        wallet_info = {
            'address': self.address,
            'created_at': time.time(),
            'public_key_file': os.path.basename(pub_key_file),
            'private_key_file': os.path.basename(priv_key_file)
        }

        info_file = os.path.join(folder_path, f"wallet_{self.address[:10]}_info.json")
        with open(info_file, 'w') as f:
            json.dump(wallet_info, f, indent=4)

        print(f"Wallet saved to {folder_path}")
        return True

    @classmethod
    def load_wallet(cls, private_key_path, blockchain=None, password=None):
        """Load wallet from a saved private key file."""
        private_key = load_key_from_file(private_key_path, is_private=True, password=password)
        public_key = private_key.public_key()
        wallet = cls(private_key=private_key, public_key=public_key, blockchain=blockchain)
        wallet._generate_address()
        return wallet

    def create_transaction(self, receiver_address, amount):
        from blockchain.transaction import Transaction
        if not self.blockchain:
            raise ValueError("Blockchain reference is required.")
        if self.get_balance() < amount:
            raise ValueError("Insufficient balance.")

        tx = Transaction(sender=self.address, receiver=receiver_address, amount=amount)
        self.sign_transaction(tx)
        return tx

    def sign_transaction(self, transaction):
        if not self.private_key:
            raise ValueError("Private key is required.")
        return transaction.sign_transaction(self.private_key)

    def get_balance(self):
        if not self.blockchain:
            raise ValueError("Blockchain reference is required.")
        return self.blockchain.get_balance(self.address)

    def get_transaction_history(self):
        if not self.blockchain:
            raise ValueError("Blockchain reference is required.")

        txs = []
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.sender == self.address or tx.receiver == self.address:
                    txs.append({
                        'tx_id': tx.tx_id,
                        'timestamp': tx.timestamp,
                        'amount': tx.amount,
                        'type': "sent" if tx.sender == self.address else "received",
                        'counterparty': tx.receiver if tx.sender == self.address else tx.sender,
                        'block_index': block.index
                    })
        return sorted(txs, key=lambda x: x['timestamp'], reverse=True)

    def __repr__(self):
        balance = self.get_balance() if self.blockchain else "unknown"
        return f"Wallet(address={self.address}, balance={balance})"


if __name__ == "__main__":
    # print("Running wallet module...")
    # wallet = Wallet()
    # print("📬 Wallet Address:", wallet.address)
    # print("🔐 Private Key:", wallet.private_key)
    # print("💰 Balance:", wallet.get_balance())
    # tx = wallet.create_transaction("recipient_address", 2.0)
    # print("✅ Created transaction:", tx.to_dict())

    # wallet.save_wallet(folder_path=".")
    # print(wallet)


    from blockchain.blockchain import Blockchain
    from wallet.wallet import Wallet

    blockchain = Blockchain()
    wallet = Wallet()
    wallet.blockchain = blockchain
    blockchain.mine_block(wallet.address)

    print("📬 Wallet Address:", wallet.address)
    print("💰 Balance:", wallet.get_balance())  # Should be 0.0

