import hashlib
import time

def proof_of_work(block, difficulty=4):
    """
    Perform Proof of Work algorithm to find a valid hash.
    
    Args:
        block: The Block object to mine
        difficulty: Number of leading zeros required in hash
        
    Returns:
        dict or None: Dictionary with nonce and hash if successful, None if interrupted
    """
    target = '0' * difficulty
    max_nonce = 2**32  # 4 billion
    
    print(f"Mining block {block.index} with difficulty {difficulty}...")
    start_time = time.time()
    
    for nonce in range(max_nonce):
        # Update block's nonce
        block.nonce = nonce
        
        # Calculate new hash
        block_hash = block.calculate_hash()
        
        # Check if hash meets difficulty requirement
        if block_hash.startswith(target):
            end_time = time.time()
            mining_time = end_time - start_time
            print(f"Block mined in {mining_time:.2f} seconds! Nonce: {nonce}, Hash: {block_hash}")
            
            return {
                'nonce': nonce,
                'hash': block_hash
            }
        
        # Print progress every million attempts
        if nonce % 1000000 == 0 and nonce > 0:
            elapsed = time.time() - start_time
            print(f"Still mining... {nonce:,} hashes checked ({nonce/elapsed:.2f} h/s)")
        
        # Check if mining should be interrupted (could expand for better control)
        if nonce % 10000 == 0 and hasattr(block, 'interrupt_mining') and block.interrupt_mining:
            print("Mining interrupted!")
            return None
    
    print("Reached maximum nonce value without finding valid hash")
    return None

def is_valid_proof(block, difficulty=4):
    """
    Check if a block's hash meets the proof-of-work difficulty requirement.
    
    Args:
        block: The Block object to check
        difficulty: Number of leading zeros required in hash
        
    Returns:
        bool: True if the block's hash meets the difficulty requirement
    """
    # The block hash should start with 'difficulty' number of zeros
    target = '0' * difficulty
    
    # Check if the hash was calculated correctly and meets the difficulty
    return (block.hash == block.calculate_hash() and 
            block.hash.startswith(target))