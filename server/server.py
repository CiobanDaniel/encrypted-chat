import socket
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import HOST, PORT, BUFFER_SIZE

clients = []

def handle_client(conn, addr):
    print(f"[NOU] Conexiune stabilita cu {addr}")
    clients.append(conn)
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
                
            print(f"[SERVER ROUTER] Am primit {len(data)} bytes criptați. Retrimit...")
            broadcast(data, conn)
            
    except ConnectionResetError:
        pass
    finally:
        print(f"[DECONECTARE] {addr} a iesit.")
        clients.remove(conn)
        conn.close()

def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.sendall(message)
            except Exception:
                clients.remove(client)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[*] Server pornit pe {HOST}:{PORT}. Astept conexiuni...")
    
    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Server oprit.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()