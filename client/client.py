import socket
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import HOST, PORT, BUFFER_SIZE
from crypto_utils import generate_keypair, derive_aes_key, encrypt_message, decrypt_message

shared_aes_key = None

def receive_messages(sock, my_private_key, my_public_bytes):
    global shared_aes_key
    
    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
                
            if data.startswith(b"PUBKEY:"):
                peer_pub_bytes = data[7:]

                if shared_aes_key is None:
                    shared_aes_key = derive_aes_key(my_private_key, peer_pub_bytes)
                    print("\n[!] Cheie E2EE negociata cu succes! Conversatia este acum sigura.")
                    print(">>> ", end="", flush=True)
                    
                    sock.sendall(b"PUBKEY:" + my_public_bytes)
            
            elif shared_aes_key:
                decrypted_message = decrypt_message(shared_aes_key, data)
                print(f"\n[PARTENER]: {decrypted_message}")
                print(">>> ", end="", flush=True)
            else:
                print("\n[!] Am primit un mesaj, dar cheia de criptare nu a fost negociata inca.")
                print(">>> ", end="", flush=True)
                
        except Exception as e:
            print(f"\n[EROARE]: {e}")
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        print("[*] Conectat la server.")
    except ConnectionRefusedError:
        print("[!] Eroare: Serverul nu este pornit!")
        return

    print("[*] Generez cheile criptografice...")
    my_private_key, my_public_bytes = generate_keypair()
    
    client.sendall(b"PUBKEY:" + my_public_bytes)

    receive_thread = threading.Thread(target=receive_messages, args=(client, my_private_key, my_public_bytes))
    receive_thread.daemon = True
    receive_thread.start()

    print(">>> Asteptam conectarea unui partener pentru a negocia cheia... (Poti scrie 'exit' pentru a iesi)")
    try:
        while True:
            message = input()
            if message.lower() == 'exit':
                break
            
            if message:
                if shared_aes_key is None:
                    print("[!] Nu poti trimite mesaje pana nu se conecteaza un partener si negociati cheia!")
                else:
                    encrypted_data = encrypt_message(shared_aes_key, message)
                    client.sendall(encrypted_data)
    except KeyboardInterrupt:
        pass
    finally:
        client.close()
        print("\n[*] Deconectat.")

if __name__ == "__main__":
    start_client()