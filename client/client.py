import socket
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import HOST, PORT, BUFFER_SIZE
from crypto_utils import generate_keypair, derive_aes_key, encrypt_message, decrypt_message

active_sessions = {}
current_chat_partner = None

def receive_messages(sock, my_private_key, my_public_bytes):
    global current_chat_partner
    
    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
                
            if data.startswith(b"SERVER:"):
                print(f"\n[SERVER]: {data[7:].decode('utf-8')}")
                print(">>> ", end="", flush=True)
                continue
            
            if data.startswith(b"FROM:"):
                parts = data.split(b":", 2)
                if len(parts) < 3: 
                    continue
                
                sender = parts[1].decode('utf-8')
                payload = parts[2]
                
                if payload.startswith(b"PUBKEY:"):
                    peer_pub_bytes = payload[7:]
                    aes_key = derive_aes_key(my_private_key, peer_pub_bytes)
                    active_sessions[sender] = aes_key
                    
                    print(f"\n[!] {sender} a initiat o conexiune E2EE. Cheie calculata. Raspund...")
                    reply = f"ROUTE:{sender}:".encode('utf-8') + b"PUBKEY_REPLY:" + my_public_bytes
                    sock.sendall(reply)
                    print(">>> ", end="", flush=True)
                
                elif payload.startswith(b"PUBKEY_REPLY:"):
                    peer_pub_bytes = payload[13:]
                    aes_key = derive_aes_key(my_private_key, peer_pub_bytes)
                    active_sessions[sender] = aes_key
                    print(f"\n[!] Cheie E2EE stabilita cu {sender}! Puteti vorbi.")
                    print(">>> ", end="", flush=True)
                
                elif payload.startswith(b"MSG:"):
                    encrypted_msg = payload[4:]
                    if sender in active_sessions:
                        decrypted_text = decrypt_message(active_sessions[sender], encrypted_msg)
                        print(f"\n[{sender}]: {decrypted_text}")
                    else:
                        print(f"\n[!] Am primit date criptate de la {sender}, dar nu avem sesiunea setata.")
                    print(">>> ", end="", flush=True)

        except Exception as e:
            print(f"\n[EROARE]: {e}")
            break

def start_client():
    global current_chat_partner
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("[!] Eroare: Serverul nu este pornit!")
        return

    my_username = input("Alege un nume de utilizator: ")
    client.sendall(f"REGISTER:{my_username}".encode('utf-8'))

    print("[*] Generez cheile criptografice locale...")
    my_private_key, my_public_bytes = generate_keypair()
    
    receive_thread = threading.Thread(target=receive_messages, args=(client, my_private_key, my_public_bytes))
    receive_thread.daemon = True
    receive_thread.start()

    print("\n--- COMENZI CHAT ---")
    print(" /chat <nume>  : Incepe o conversatie securizata cu cineva")
    print(" <text>        : Trimite un mesaj persoanei cu care conversezi curent")
    print(" exit          : Inchide aplicatia\n")

    try:
        while True:
            msg = input(">>> ")
            if msg.lower() == 'exit':
                break
            
            if not msg:
                continue

            if msg.startswith("/chat "):
                target = msg.split(" ", 1)[1]
                if target == my_username:
                    print("[!] Nu poti vorbi cu tine insuti!")
                    continue
                
                current_chat_partner = target
                print(f"[*] Trimit cheia publica catre {target} pentru a negocia criptarea...")
                req = f"ROUTE:{current_chat_partner}:".encode('utf-8') + b"PUBKEY:" + my_public_bytes
                client.sendall(req)
            
            # Dacă scriem un mesaj normal
            else:
                if current_chat_partner is None:
                    print("[!] Nu ai selectat un partener. Foloseste '/chat <nume>' mai intai.")
                elif current_chat_partner not in active_sessions:
                    print(f"[!] Asteapta ca {current_chat_partner} sa raspunda la negocierea cheii.")
                else:
                    enc_data = encrypt_message(active_sessions[current_chat_partner], msg)
                    req = f"ROUTE:{current_chat_partner}:".encode('utf-8') + b"MSG:" + enc_data
                    client.sendall(req)

    except KeyboardInterrupt:
        pass
    finally:
        client.close()
        print("\n[*] Deconectat.")

if __name__ == "__main__":
    start_client()