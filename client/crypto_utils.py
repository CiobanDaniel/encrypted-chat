import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def generate_keypair():
    """Genereaza o pereche de chei (Privata si Publica) folosind Curbe Eliptice."""
    private_key = ec.generate_private_key(ec.SECP384R1())
    public_key = private_key.public_key()
    
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_key, public_bytes

def derive_aes_key(private_key, peer_public_bytes) -> bytes:
    """Foloseste cheia privata proprie si cheia publica a partenerului pentru a genera cheia AES."""
    peer_public_key = serialization.load_pem_public_key(peer_public_bytes)
    
    shared_secret = private_key.exchange(ec.ECDH(), peer_public_key)

    aes_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake chat',
    ).derive(shared_secret)
    
    return aes_key

def encrypt_message(aes_key: bytes, message: str) -> bytes:
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12) 
    ciphertext = aesgcm.encrypt(nonce, message.encode('utf-8'), None)
    return nonce + ciphertext

def decrypt_message(aes_key: bytes, encrypted_data: bytes) -> str:
    aesgcm = AESGCM(aes_key)
    nonce = encrypted_data[:12] 
    ciphertext = encrypted_data[12:] 
    decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_data.decode('utf-8')