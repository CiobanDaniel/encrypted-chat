import socket
import threading
import sys
import os
import secrets
import time
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import SERVER_BIND_HOST, SERVER_BIND_PORT, BUFFER_SIZE
from shared.protocol import build_from, build_server_message, parse_register_packet, parse_route
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

clients = {}
clients_by_username = {}
client_metadata = {}
pending_link_requests = {}


def _client_key(username, device_id):
    return f"{username}::{device_id}"


def _register_connection(username, device_id, conn, register_data):
    key = _client_key(username, device_id)
    clients[key] = conn
    client_metadata[key] = register_data
    clients_by_username.setdefault(username, set()).add(key)


def _unregister_connection(username, device_id):
    key = _client_key(username, device_id)
    clients.pop(key, None)
    client_metadata.pop(key, None)
    if username in clients_by_username:
        clients_by_username[username].discard(key)
        if not clients_by_username[username]:
            del clients_by_username[username]


def _notify_device(username, device_id, message):
    key = _client_key(username, device_id)
    target_conn = clients.get(key)
    if target_conn:
        target_conn.sendall(build_server_message(message))


def _first_device_for_username(username):
    keys = sorted(list(clients_by_username.get(username, set())))
    if not keys:
        return None
    first = keys[0]
    return client_metadata.get(first)


def _build_link_approval_text(owner_username, link_token, target_device_id):
    return f"LINK_APPROVAL:{owner_username}:{link_token}:{target_device_id}"


def _verify_signature(identity_key_b64, approval_text, signature_b64):
    try:
        public_bytes = base64.b64decode(identity_key_b64.encode("ascii"))
        signature = base64.b64decode(signature_b64.encode("ascii"))
        pub_key = serialization.load_pem_public_key(public_bytes)
        pub_key.verify(signature, approval_text.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
        return True
    except (ValueError, InvalidSignature):
        return False

def handle_client(conn, addr):
    username = None
    device_id = None
    try:
        initial_data = conn.recv(BUFFER_SIZE)
        register_data = parse_register_packet(initial_data)
        if register_data:
            username = register_data["username"]
            device_id = register_data.get("device_id") or secrets.token_hex(4)
            register_data["device_id"] = device_id
            _register_connection(username, device_id, conn, register_data)
            print(f"[+] {username}/{device_id} s-a conectat de la {addr}")
            conn.sendall(build_server_message("Te-ai inregistrat cu succes!"))
        else:
            print(f"[!] Conexiune respinsa de la {addr} (Nu s-a inregistrat corect)")
            conn.close()
            return

        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break

            try:
                text_data = data.decode("utf-8")
            except UnicodeDecodeError:
                text_data = ""

            if text_data.startswith("LINK_CREATE:"):
                # LINK_CREATE:<username>:<device_id>
                parts = text_data.split(":", 2)
                if len(parts) == 3 and parts[1] == username and parts[2] == device_id:
                    code = secrets.token_hex(3).upper()
                    pending_link_requests[(username, code)] = {
                        "creator_device_id": device_id,
                        "created_at": int(time.time()),
                    }
                    conn.sendall(build_server_message(f"LINK_CODE:{code}"))
                continue

            if text_data.startswith("LINK_CONSUME:"):
                # LINK_CONSUME:<username>:<code>:<new_device_id>
                parts = text_data.split(":", 3)
                if len(parts) == 4:
                    link_username, code, new_device_id = parts[1], parts[2], parts[3]
                    req_key = (link_username, code)
                    request = pending_link_requests.get(req_key)
                    if request:
                        link_token = secrets.token_hex(12)
                        request["target_device_id"] = new_device_id
                        request["link_token"] = link_token
                        request["requester_username"] = username
                        request["requester_device_id"] = device_id
                        request["approved"] = False

                        creator_device_id = request.get("creator_device_id", "")
                        _notify_device(
                            link_username,
                            creator_device_id,
                            f"LINK_APPROVAL_REQUEST:{link_token}:{new_device_id}:{code}",
                        )
                        conn.sendall(build_server_message("LINK_PENDING:Astept aprobare de pe device-ul principal."))
                    else:
                        conn.sendall(build_server_message("LINK_ERR:Cod invalid sau expirat."))
                continue

            if text_data.startswith("LINK_APPROVE_SIG:"):
                # LINK_APPROVE_SIG:<username>:<link_token>:<signature_b64>
                parts = text_data.split(":", 3)
                if len(parts) == 4:
                    owner_username, link_token, signature_b64 = parts[1], parts[2], parts[3]
                    matched_key = None
                    for key, request in pending_link_requests.items():
                        if key[0] == owner_username and request.get("link_token") == link_token:
                            matched_key = key
                            break
                    if matched_key is None:
                        conn.sendall(build_server_message("LINK_ERR:Cererea de aprobare nu exista."))
                        continue
                    request = pending_link_requests[matched_key]
                    if request.get("creator_device_id") != device_id:
                        conn.sendall(build_server_message("LINK_ERR:Doar device-ul principal poate aproba."))
                        continue
                    account_meta = _first_device_for_username(owner_username) or {}
                    account_id = account_meta.get("account_id", "")
                    creator_identity = account_meta.get("identity_key_b64", "")
                    target_device_id = request.get("target_device_id", "")
                    approval_text = _build_link_approval_text(owner_username, link_token, target_device_id)
                    if not _verify_signature(creator_identity, approval_text, signature_b64):
                        conn.sendall(build_server_message("LINK_ERR:Semnatura de aprobare invalida."))
                        continue
                    request["approved"] = True
                    requester_user = request.get("requester_username", owner_username)
                    requester_device = request.get("requester_device_id", "")
                    requester_key = _client_key(requester_user, requester_device)
                    requester_conn = clients.get(requester_key)
                    if requester_conn:
                        requester_conn.sendall(
                            build_server_message(
                                f"LINK_APPROVED:{account_id}:{creator_identity}:{owner_username}:{link_token}:{target_device_id}:{signature_b64}"
                            )
                        )
                    conn.sendall(build_server_message("LINK_INFO:Cerere aprobata."))
                    pending_link_requests.pop(matched_key, None)
                continue

            route_data = parse_route(data)
            if route_data:
                target_user, payload = route_data
                target_keys = list(clients_by_username.get(target_user, set()))
                if target_keys:
                    for target_key in target_keys:
                        target_conn = clients.get(target_key)
                        if target_conn:
                            target_conn.sendall(build_from(username, payload))
                    print(f"[ROUTER] Rutat pachet de la {username}/{device_id} catre {target_user} ({len(target_keys)} device-uri)")
                else:
                    conn.sendall(build_server_message(f"Utilizatorul '{target_user}' nu este online."))

    except Exception as e:
        print(f"[WARN] Eroare in handle_client pentru {addr}: {e}")
    finally:
        if username and device_id:
            _unregister_connection(username, device_id)
            print(f"[-] {username}/{device_id} s-a deconectat.")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((SERVER_BIND_HOST, SERVER_BIND_PORT))
    server.listen()
    
    server.settimeout(1.0)
    
    print(f"[*] Serverul de Rutare E2EE pornit pe {SERVER_BIND_HOST}:{SERVER_BIND_PORT}")
    
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