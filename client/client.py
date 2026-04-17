import socket
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import HOST, PORT, BUFFER_SIZE
from crypto_utils import encrypt_message, decrypt_message

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
            decrypted_message = decrypt_message(data)
            print(f"\n[PARTENER]: {decrypted_message}")
        except Exception as e:
            print(f"\n[EROARE DE CRIPTARE/RETEA]: {e}")
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        print("[*] Conectat la serverul securizat.")
    except ConnectionRefusedError:
        print("[!] Eroare: Serverul nu este pornit!")
        return

    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.daemon = True
    receive_thread.start()

    print(">>> Poti scrie mesaje. Scrie 'exit' pentru a iesi.")
    try:
        while True:
            message = input()
            if message.lower() == 'exit':
                break
            if message:
                encrypted_data = encrypt_message(message)
                client.sendall(encrypted_data)
    except KeyboardInterrupt:
        pass
    finally:
        client.close()
        print("[*] Deconectat.")

if __name__ == "__main__":
    start_client()