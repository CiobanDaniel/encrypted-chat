import socket
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import HOST, PORT, BUFFER_SIZE

clients = {} 

def handle_client(conn, addr):
    username = None
    try:
        initial_data = conn.recv(BUFFER_SIZE).decode('utf-8')
        if initial_data.startswith("REGISTER:"):
            username = initial_data.split(":")[1]
            clients[username] = conn
            print(f"[+] {username} s-a conectat de la {addr}")
            conn.sendall(b"SERVER:Te-ai inregistrat cu succes!")
        else:
            print(f"[!] Conexiune respinsa de la {addr} (Nu s-a inregistrat corect)")
            conn.close()
            return

        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            
            parts = data.split(b":", 2)
            if len(parts) == 3 and parts[0] == b"ROUTE":
                target_user = parts[1].decode('utf-8')
                payload = parts[2]
                
                if target_user in clients:
                    header = f"FROM:{username}:".encode('utf-8')
                    clients[target_user].sendall(header + payload)
                    print(f"[ROUTER] Rutat pachet de la {username} catre {target_user}")
                else:
                    error_msg = f"SERVER:Utilizatorul '{target_user}' nu este online."
                    conn.sendall(error_msg.encode('utf-8'))

    except Exception:
        pass
    finally:
        if username and username in clients:
            del clients[username]
            print(f"[-] {username} s-a deconectat.")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen()
    
    server.settimeout(1.0)
    
    print(f"[*] Serverul de Rutare E2EE pornit pe {HOST}:{PORT}")
    
    try:
        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C detectat! Serverul se opreste...")
    finally:
        server.close()
        print("[*] Server oprit complet.")

if __name__ == "__main__":
    start_server()