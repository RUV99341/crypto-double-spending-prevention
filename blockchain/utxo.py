class UTXO:
    def __init__(self, transaction_id, output_index, amount, owner_address):
        """
        Initialize a UTXO (Unspent Transaction Output).
        
        Args:
            transaction_id: The ID of the transaction that created this output
            output_index: The index of this output in the transaction
            amount: The amount of cryptocurrency in this output
            owner_address: The address/public key of the owner of this output
        """
        self.transaction_id = transaction_id
        self.output_index = output_index
        self.amount = amount
        self.owner_address = owner_address
    
    def to_dict(self):
        """Convert UTXO to a dictionary."""
        return {
            'transaction_id': self.transaction_id,
            'output_index': self.output_index,
            'amount': self.amount,
            'owner_address': self.owner_address
        }
    
    def __repr__(self):
        """Debug-friendly string representation."""
        return (f"UTXO(tx_id={self.transaction_id[:10]}..., "
                f"idx={self.output_index}, "
                f"amount={self.amount}, "
                f"owner={self.owner_address[:10]}...)")


class UTXOSet:
    def __init__(self):
        """Initialize a new UTXO set to track unspent outputs."""
        # Organized as: {address: {tx_id_output_idx: UTXO}}
        self.utxos = {}
    
    def add_utxo(self, utxo):
        """
        Add a UTXO to the set.
        
        Args:
            utxo: The UTXO object to add
            
        Returns:
            bool: True if the UTXO was added, False if it already exists
        """
        # only for checking purposes
        print(f"💾 Adding UTXO: {utxo}")

        address = utxo.owner_address
        utxo_key = f"{utxo.transaction_id}_{utxo.output_index}"
        
        if address not in self.utxos:
            self.utxos[address] = {}
        
        if utxo_key in self.utxos[address]:
            return False  # UTXO already exists
        
        self.utxos[address][utxo_key] = utxo
        return True
    
    def spend_utxo(self, transaction_id, output_index, owner_address):
        """
        Mark a UTXO as spent by removing it from the set.
        
        Args:
            transaction_id: Transaction ID of the UTXO
            output_index: Output index of the UTXO
            owner_address: Address of the owner
            
        Returns:
            UTXO or None: The spent UTXO if found and removed, None otherwise
        """
        if owner_address not in self.utxos:
            return None
        
        utxo_key = f"{transaction_id}_{output_index}"
        utxo = self.utxos[owner_address].pop(utxo_key, None)
        
        # Clean up empty address entries
        if not self.utxos[owner_address]:
            self.utxos.pop(owner_address)
        
        return utxo
    
    def get_utxos(self, address):
        """
        Get all UTXOs for a specific address.
        
        Args:
            address: The wallet address to get UTXOs for
            
        Returns:
            list: List of UTXO objects owned by the address
        """
        # print("hello ritesh")
        if address not in self.utxos:
            return []
        
        return list(self.utxos[address].values())
    
    def get_balance(self, address):
        """
        Calculate the total balance for an address.
        
        Args:
            address: The wallet address to calculate balance for
            
        Returns:
            float: The total balance
        """
        if address not in self.utxos:
            return 0.0
        
        return sum(utxo.amount for utxo in self.utxos[address].values())
    
    def is_unspent(self, transaction_id, output_index, address):
        """
        Check if a specific UTXO is unspent.
        
        Args:
            transaction_id: Transaction ID of the UTXO
            output_index: Output index of the UTXO
            address: Address of the owner
            
        Returns:
            bool: True if the UTXO is unspent, False otherwise
        """
        if address not in self.utxos:
            return False
        
        utxo_key = f"{transaction_id}_{output_index}"
        return utxo_key in self.utxos[address]
    
    def update_utxos(self, transaction):
        """
        Update the UTXO set after processing a transaction.
        
        Args:
            transaction: The transaction to process
            
        Returns:
            bool: True if successful, False if inputs are invalid
        """
        # only for checking purposes
        print(f"\n🧪 update_utxos() called for tx: {transaction.tx_id}")
        print(f"    sender: {transaction.sender}")
        print(f"    receiver: {transaction.receiver}")
        print(f"    amount: {transaction.amount}")
        # For mining rewards (no inputs to validate)
        if str(transaction.sender) == "0":
            # only for checking purposes
            print("    ✅ Detected coinbase tx - creating UTXO")
            # Add the output to the receiver
            new_utxo = UTXO(
                transaction_id=transaction.tx_id,
                output_index=0,
                amount=transaction.amount,
                owner_address=transaction.receiver
            )
            self.add_utxo(new_utxo)
            return True
        
        # Regular transaction processing
        # Check that all inputs are valid
        # Simplified for now - in a real system we'd need to actually reference specific UTXOs
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance < transaction.amount:
            return False  # Insufficient balance
        
        # Spend UTXOs (simplified - we'd normally select specific UTXOs)
        # For now, we'll just reduce the sender's balance by spending the first UTXOs we find
        amount_to_spend = transaction.amount
        sender_utxos = self.get_utxos(transaction.sender)
        
        for utxo in sender_utxos:
            if amount_to_spend <= 0:
                break
                
            if utxo.amount <= amount_to_spend:
                # Spend this UTXO completely
                self.spend_utxo(utxo.transaction_id, utxo.output_index, transaction.sender)
                amount_to_spend -= utxo.amount
            else:
                # Spend part of this UTXO and create change
                self.spend_utxo(utxo.transaction_id, utxo.output_index, transaction.sender)
                
                # Create a change UTXO for sender
                change_amount = utxo.amount - amount_to_spend
                change_utxo = UTXO(
                    transaction_id=transaction.tx_id,
                    output_index=1,  # By convention, output 1 is change
                    amount=change_amount,
                    owner_address=transaction.sender
                )
                self.add_utxo(change_utxo)
                
                amount_to_spend = 0
        
        # Create output UTXO for receiver
        output_utxo = UTXO(
            transaction_id=transaction.tx_id,
            output_index=0,  # By convention, output 0 is payment
            amount=transaction.amount,
            owner_address=transaction.receiver
        )
        self.add_utxo(output_utxo)
        
        return True
    
    def __repr__(self):
        """Debug-friendly string representation."""
        total_utxos = sum(len(addr_utxos) for addr_utxos in self.utxos.values())
        return f"UTXOSet(addresses={len(self.utxos)}, utxos={total_utxos})"



   
if __name__ == "__main__":
    from blockchain.transaction import Transaction

    class DummyTx:
        def __init__(self, sender, receiver, amount, tx_id):
            self.sender = sender
            self.receiver = receiver
            self.amount = amount
            self.tx_id = tx_id

    utxo_set = UTXOSet()

    coinbase = DummyTx("0", "wallet1", 5.0, "coinbase_tx")
    assert utxo_set.update_utxos(coinbase)
    assert utxo_set.get_balance("wallet1") == 5.0

    tx1 = DummyTx("wallet1", "wallet2", 3.0, "tx1")
    assert utxo_set.update_utxos(tx1)
    assert utxo_set.get_balance("wallet1") == 2.0  # change
    assert utxo_set.get_balance("wallet2") == 3.0

    print("✅ All UTXO tests passed.")
