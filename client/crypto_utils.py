import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HARDCODED_KEY = b'12345678901234567890123456789012' 

def encrypt_message(message: str) -> bytes:
    aesgcm = AESGCM(HARDCODED_KEY)
    # AES-GCM 'nonce' (12 bytes). 
    nonce = os.urandom(12) 
    
    ciphertext = aesgcm.encrypt(nonce, message.encode('utf-8'), None)
    
    return nonce + ciphertext

def decrypt_message(encrypted_data: bytes) -> str:
    aesgcm = AESGCM(HARDCODED_KEY)
    
    nonce = encrypted_data[:12] 
    ciphertext = encrypted_data[12:] 
    
    decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
    
    return decrypted_data.decode('utf-8')