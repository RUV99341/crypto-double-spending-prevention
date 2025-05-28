import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_key_pair():
    """
    Generate a new RSA key pair for cryptocurrency wallet.
    
    Returns:
        tuple: (private_key, public_key) as cryptography objects
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    return private_key, public_key

def save_key_to_file(key, filename, is_private=True, password=None):
    """
    Save a key to a file.
    
    Args:
        key: The cryptography key object
        filename: Path to save the key
        is_private: Whether the key is a private key
        password: Password to encrypt the private key (optional)
        
    Returns:
        bool: True if successful
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    
    if is_private:
        # Serialize private key
        if password:
            # Use password encryption
            encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
        else:
            # No encryption
            encryption_algorithm = serialization.NoEncryption()
        
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
    else:
        # Serialize public key
        pem = key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    # Write key to file
    with open(filename, 'wb') as f:
        f.write(pem)
    
    return True

def load_key_from_file(filename, is_private=True, password=None):
    """
    Load a key from a file.
    
    Args:
        filename: Path to the key file
        is_private: Whether the key is a private key
        password: Password to decrypt the private key (if needed)
        
    Returns:
        The loaded key as a cryptography object
    """
    # Read key from file
    with open(filename, 'rb') as f:
        pem_data = f.read()
    
    if is_private:
        # Load private key
        if password:
            # Use password for decryption
            key = serialization.load_pem_private_key(
                pem_data,
                password=password.encode(),
                backend=default_backend()
            )
        else:
            # No password
            key = serialization.load_pem_private_key(
                pem_data,
                password=None,
                backend=default_backend()
            )
    else:
        # Load public key
        key = serialization.load_pem_public_key(
            pem_data,
            backend=default_backend()
        )
    
    return key

def serialize_public_key(public_key):
    """
    Convert a public key to a string format suitable for transmission.
    
    Args:
        public_key: The public key object
        
    Returns:
        str: PEM encoded public key
    """
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

def deserialize_public_key(pem_string):
    """
    Convert a PEM string back to a public key object.
    
    Args:
        pem_string: PEM encoded public key string
        
    Returns:
        The public key object
    """
    pem_bytes = pem_string.encode('utf-8')
    public_key = serialization.load_pem_public_key(
        pem_bytes,
        backend=default_backend()
    )
    return public_key