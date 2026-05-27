import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import constant_time
from cryptography.exceptions import InvalidSignature

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


def compute_safety_number(my_public_bytes: bytes, peer_public_bytes: bytes) -> str:
    """Return a stable fingerprint for the pair of identities.

    The same two keys produce the same value on both ends, regardless of order.
    """
    first, second = sorted([my_public_bytes, peer_public_bytes])
    digest = hashes.Hash(hashes.SHA256())
    digest.update(first)
    digest.update(second)
    raw = digest.finalize().hex()[:60]
    return " ".join(raw[i : i + 5] for i in range(0, len(raw), 5))


def bytes_equal(a: bytes, b: bytes) -> bool:
    return bool(constant_time.bytes_eq(a, b))


def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64_decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def sign_link_approval(private_key, approval_text: str) -> str:
    signature = private_key.sign(approval_text.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return b64_encode(signature)


def verify_link_approval(peer_public_bytes: bytes, approval_text: str, signature_b64: str) -> bool:
    try:
        public_key = serialization.load_pem_public_key(peer_public_bytes)
        signature = b64_decode(signature_b64)
        public_key.verify(signature, approval_text.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError):
        return False