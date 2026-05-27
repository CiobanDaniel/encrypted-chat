# client/client.py
import socket
import threading
import sys
import os
import base64
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import CLIENT_SERVER_HOST, CLIENT_SERVER_PORT, BUFFER_SIZE
from shared.protocol import (
    PAYLOAD_MSG,
    PAYLOAD_PUBKEY,
    PAYLOAD_PUBKEY_REPLY,
    build_register_json,
    build_route,
    parse_from,
    parse_server_message,
)
from crypto_utils import (
    bytes_equal,
    b64_encode,
    compute_safety_number,
    derive_aes_key,
    encrypt_message,
    decrypt_message,
    sign_link_approval,
    verify_link_approval,
)
from identity_store import IdentityStore
from profile_store import ProfileStore
from session_store import SessionStore
from chat_archive_store import ChatArchiveStore
from backup_utils import build_encrypted_backup, load_encrypted_backup

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SecureChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SecureChat E2EE")
        self.geometry("900x600")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_socket = None
        self.username = None
        self.my_private_key = None
        self.my_public_bytes = None
        self.identity_store = IdentityStore()
        self.profile_store = ProfileStore()
        self.chat_archive_store = ChatArchiveStore()
        self.profile = {}
        
        # Store izolat pentru sesiuni/mesaje; ulterior poate fi inlocuit cu persistent storage.
        self.session_store = SessionStore()
        self.chat_buttons = {}     # { "Bob": <obiect_buton> }
        
        self.current_partner = None
        self.pending_link_approvals = {}
        self.session_store.import_messages(self.chat_archive_store.load_archive())

        self.show_login_screen()

    def show_login_screen(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(pady=150, padx=200, fill="both", expand=True)

        ctk.CTkLabel(self.login_frame, text="Autentificare SecureChat", font=("Arial", 24, "bold")).pack(pady=20)
        
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Alege un nume de utilizator", width=250)
        self.username_entry.pack(pady=10)
        self.username_entry.bind("<Return>", lambda event: self.connect_to_server())
        
        self.login_btn = ctk.CTkButton(self.login_frame, text="Conectare", command=self.connect_to_server)
        self.login_btn.pack(pady=20)
        
        self.error_label = ctk.CTkLabel(self.login_frame, text="", text_color="red")
        self.error_label.pack()

    def connect_to_server(self):
        self.username = self.username_entry.get().strip()
        if not self.username:
            self.error_label.configure(text="Numele nu poate fi gol!")
            return

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((CLIENT_SERVER_HOST, CLIENT_SERVER_PORT))
        except Exception:
            self.error_label.configure(text="Eroare: Server offline!")
            return

        self.my_private_key, self.my_public_bytes = self.identity_store.load_or_create_identity_keypair()
        self.profile = self.profile_store.load_or_create_profile(self.username)
        self.client_socket.sendall(
            build_register_json(
                username=self.username,
                account_id=self.profile.get("account_id", ""),
                device_id=self.profile.get("device_id", ""),
                account_mode=self.profile.get("account_mode", "anonymous"),
                identity_key_b64=b64_encode(self.my_public_bytes),
                linked_email=self.profile.get("linked_email", ""),
                linked_phone=self.profile.get("linked_phone", ""),
            )
        )

        threading.Thread(target=self.receive_messages, daemon=True).start()

        self.login_frame.destroy()
        self.show_chat_screen()

    def show_chat_screen(self):
        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        ctk.CTkLabel(self.sidebar_frame, text=f"Logat ca: {self.username}", font=("Arial", 16, "bold"), text_color="#1f6aa5").pack(pady=(20, 10))
        
        # Cautare partener nou
        self.partner_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Cauta nume...")
        self.partner_entry.pack(pady=5, padx=10, fill="x")
        self.partner_entry.bind("<Return>", lambda event: self.initiate_chat())
        
        self.start_chat_btn = ctk.CTkButton(self.sidebar_frame, text="Deschide Chat", command=self.initiate_chat)
        self.start_chat_btn.pack(pady=5, padx=10, fill="x")

        self.verify_btn = ctk.CTkButton(self.sidebar_frame, text="Verifica contact", command=self.verify_current_contact)
        self.verify_btn.pack(pady=(5, 5), padx=10, fill="x")
        self.show_number_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Arata safety number",
            command=self.show_safety_numbers,
        )
        self.show_number_btn.pack(pady=5, padx=10, fill="x")
        self.reset_trust_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Reseteaza verificare",
            command=self.reset_current_contact_verification,
        )
        self.reset_trust_btn.pack(pady=(5, 10), padx=10, fill="x")
        self.export_backup_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Export backup",
            command=self.export_encrypted_backup,
        )
        self.export_backup_btn.pack(pady=5, padx=10, fill="x")
        self.import_backup_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Import backup",
            command=self.import_encrypted_backup,
        )
        self.import_backup_btn.pack(pady=(5, 12), padx=10, fill="x")
        self.generate_link_code_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Genereaza cod link device",
            command=self.generate_device_link_code,
        )
        self.generate_link_code_btn.pack(pady=5, padx=10, fill="x")
        self.link_device_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Link acest device",
            command=self.link_this_device_to_account,
        )
        self.link_device_btn.pack(pady=(5, 12), padx=10, fill="x")
        
        # Lista de conversatii active (Tab-uri)
        ctk.CTkLabel(self.sidebar_frame, text="Conversatii Active:", text_color="gray").pack(pady=(15, 0))
        self.contacts_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.contacts_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- MAIN CHAT AREA ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Nicio conversatie deschisa", font=("Arial", 14))
        self.status_label.pack(pady=10)
        self.verify_status_label = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 12), text_color="gray")
        self.verify_status_label.pack(pady=(0, 8))

        self.chat_history = ctk.CTkTextbox(self.main_frame, state="disabled")
        self.chat_history.pack(pady=5, padx=10, fill="both", expand=True)

        self.input_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.input_frame.pack(fill="x", padx=10, pady=10)
        self.input_frame.pack_propagate(False)

        self.msg_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Scrie un mesaj...")
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        self.send_btn = ctk.CTkButton(self.input_frame, text="Trimite", width=80, command=self.send_message)
        self.send_btn.pack(side="right")

    # --- LOGICA DE UI PENTRU CHAT-URI ---

    def add_contact_tab(self, target_user):
        """Adauga un buton in lista din stanga daca nu exista deja."""
        if target_user not in self.chat_buttons:
            self.session_store.ensure_contact(target_user)
            btn = ctk.CTkButton(self.contacts_frame, text=target_user, fg_color="transparent", 
                                hover_color="#2c2c2c", anchor="w",
                                command=lambda u=target_user: self.switch_chat(u))
            btn.pack(fill="x", pady=2)
            self.chat_buttons[target_user] = btn

    def switch_chat(self, target_user):
        """Schimba contextul conversatiei catre utilizatorul selectat."""
        self.current_partner = target_user
        self.status_label.configure(text=f"Conversatie cu: {target_user}", text_color="#2FA572")
        self.refresh_verification_status(target_user)
        
        # Resetam culoarea butonului (in caz ca era evidentiat pentru mesaj necitit)
        self.chat_buttons[target_user].configure(fg_color="#1f6aa5")

        # Reincarcam istoricul mesajelor pentru acest utilizator
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        for msg in self.session_store.get_messages(target_user):
            self.chat_history.insert("end", msg + "\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    def save_and_display_message(self, user, message, is_system=False):
        """Salveaza mesajul in istoric si il afiseaza daca acel chat e deschis curent."""
        # Ne asiguram ca utilizatorul are tab
        self.add_contact_tab(user)
        
        self.session_store.add_message(user, message)

        if self.current_partner == user:
            # Afisam pe ecran daca suntem in chat-ul cu el
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", message + "\n")
            self.chat_history.see("end")
            self.chat_history.configure(state="disabled")
        elif not is_system:
            # Daca nu suntem in chat cu el si nu e mesaj de sistem, evidentiem butonul!
            self.chat_buttons[user].configure(fg_color="#8b0000") # Rosu inchis pt mesaje noi

    def initiate_chat(self):
        target = self.partner_entry.get().strip()
        if not target or target == self.username:
            return
        
        self.partner_entry.delete(0, 'end')
        self.add_contact_tab(target)
        self.switch_chat(target)
        
        if not self.session_store.has_session(target):
            self.save_and_display_message(target, "[SISTEM] Cheia publica a fost trimisa. Asteptam negocierea...", True)
            req = build_route(target, PAYLOAD_PUBKEY + self.my_public_bytes)
            self.client_socket.sendall(req)

    def refresh_verification_status(self, user: str):
        peer_pub = self.session_store.get_peer_public_key(user)
        if not peer_pub:
            self.verify_status_label.configure(text="Identitate contact: indisponibila (fara handshake)", text_color="gray")
            return

        current_fingerprint = compute_safety_number(self.my_public_bytes, peer_pub)
        trusted = self.identity_store.get_trusted_fingerprint(user)
        if trusted == current_fingerprint:
            self.verify_status_label.configure(text=f"Identitate verificata: {current_fingerprint}", text_color="#2FA572")
        else:
            self.verify_status_label.configure(text=f"Identitate neverificata: {current_fingerprint}", text_color="#d4a017")

    def verify_current_contact(self):
        if not self.current_partner:
            return
        peer_pub = self.session_store.get_peer_public_key(self.current_partner)
        if not peer_pub:
            self.save_and_display_message(
                self.current_partner,
                "[SISTEM] Nu poti verifica inca: cheia contactului nu a fost primita.",
                True,
            )
            return
        fingerprint = compute_safety_number(self.my_public_bytes, peer_pub)
        self.identity_store.set_trusted_fingerprint(self.current_partner, fingerprint)
        self.save_and_display_message(
            self.current_partner,
            f"[SISTEM] Contact verificat local. Safety number: {fingerprint}",
            True,
        )
        self.refresh_verification_status(self.current_partner)

    def show_safety_numbers(self):
        if not self.current_partner:
            messagebox.showinfo("Safety number", "Selecteaza mai intai un contact.")
            return
        peer_pub = self.session_store.get_peer_public_key(self.current_partner)
        if not peer_pub:
            messagebox.showinfo(
                "Safety number",
                "Cheia contactului nu este disponibila inca. Initiaza handshake-ul mai intai.",
            )
            return

        my_fingerprint = compute_safety_number(self.my_public_bytes, self.my_public_bytes)
        pair_fingerprint = compute_safety_number(self.my_public_bytes, peer_pub)
        messagebox.showinfo(
            "Safety numbers",
            (
                f"Contact: {self.current_partner}\n\n"
                f"Numarul tau (self-check):\n{my_fingerprint}\n\n"
                f"Numarul vostru comun:\n{pair_fingerprint}\n\n"
                "Compara numarul comun printr-un canal separat (apel/IRL)."
            ),
        )

    def reset_current_contact_verification(self):
        if not self.current_partner:
            return
        removed = self.identity_store.clear_trusted_fingerprint(self.current_partner)
        if removed:
            self.save_and_display_message(
                self.current_partner,
                "[SISTEM] Verificarea contactului a fost resetata. Refa verificarea safety number.",
                True,
            )
        else:
            self.save_and_display_message(
                self.current_partner,
                "[SISTEM] Contactul nu era verificat anterior.",
                True,
            )
        self.refresh_verification_status(self.current_partner)

    def export_encrypted_backup(self):
        path = filedialog.asksaveasfilename(
            title="Export backup criptat",
            defaultextension=".scbackup",
            filetypes=[("SecureChat Backup", "*.scbackup"), ("All files", "*.*")],
        )
        if not path:
            return
        passphrase = simpledialog.askstring(
            "Parola backup",
            "Introdu parola pentru criptarea backup-ului:",
            show="*",
        )
        if not passphrase:
            return
        payload = {
            "profile": self.profile_store.export_profile(),
            "identity": self.identity_store.export_state(),
            "chat_archive": self.session_store.export_messages(),
        }
        blob = build_encrypted_backup(passphrase, payload)
        with open(path, "wb") as f:
            f.write(blob)
        messagebox.showinfo("Backup", "Backup exportat cu succes.")

    def import_encrypted_backup(self):
        path = filedialog.askopenfilename(
            title="Import backup criptat",
            filetypes=[("SecureChat Backup", "*.scbackup"), ("All files", "*.*")],
        )
        if not path:
            return
        passphrase = simpledialog.askstring(
            "Parola backup",
            "Introdu parola backup-ului:",
            show="*",
        )
        if not passphrase:
            return
        try:
            with open(path, "rb") as f:
                blob = f.read()
            payload = load_encrypted_backup(passphrase, blob)
        except Exception:
            messagebox.showerror("Backup", "Nu am putut decripta backup-ul. Verifica parola.")
            return

        profile = payload.get("profile", {})
        identity = payload.get("identity", {})
        chat_archive = payload.get("chat_archive", {})

        if isinstance(profile, dict):
            self.profile_store.import_profile(profile)
            self.profile = self.profile_store.export_profile()
        if isinstance(identity, dict):
            self.identity_store.import_state(identity)
            self.my_private_key, self.my_public_bytes = self.identity_store.load_or_create_identity_keypair()
        if isinstance(chat_archive, dict):
            self.session_store.import_messages(chat_archive)
            self.chat_archive_store.save_archive(self.session_store.export_messages())

        self.session_store.clear_sessions()
        if self.current_partner:
            self.switch_chat(self.current_partner)
        messagebox.showinfo("Backup", "Backup importat. Sesiunile active au fost resetate.")

    def generate_device_link_code(self):
        if not self.client_socket or not self.profile:
            return
        cmd = f"LINK_CREATE:{self.username}:{self.profile.get('device_id', '')}"
        self.client_socket.sendall(cmd.encode("utf-8"))
        self.save_and_display_message(
            self.username,
            "[SISTEM] Cerere cod link trimisa catre server.",
            True,
        )

    def link_this_device_to_account(self):
        if not self.client_socket or not self.profile:
            return
        code = simpledialog.askstring(
            "Link device",
            "Introdu codul de link generat pe device-ul principal:",
        )
        if not code:
            return
        cmd = f"LINK_CONSUME:{self.username}:{code.strip().upper()}:{self.profile.get('device_id', '')}"
        self.client_socket.sendall(cmd.encode("utf-8"))

    def process_peer_key(self, sender: str, peer_pub_bytes: bytes):
        previous_key = self.session_store.get_peer_public_key(sender)
        self.session_store.set_peer_public_key(sender, peer_pub_bytes)

        current_fingerprint = compute_safety_number(self.my_public_bytes, peer_pub_bytes)
        trusted_fingerprint = self.identity_store.get_trusted_fingerprint(sender)

        if trusted_fingerprint and trusted_fingerprint != current_fingerprint:
            warning_msg = (
                f"[ALERTA] Cheia lui {sender} s-a schimbat fata de cheia verificata! "
                "Nu mai trimite mesaje sensibile pana reverifici identitatea."
            )
            self.update_ui_from_thread(self.save_and_display_message, sender, warning_msg, True)
            self.update_ui_from_thread(
                messagebox.showwarning,
                "Avertizare securitate",
                f"Cheia contactului '{sender}' s-a schimbat.\nRe-verifica safety number-ul.",
            )

        if previous_key and not bytes_equal(previous_key, peer_pub_bytes):
            self.update_ui_from_thread(
                self.save_and_display_message,
                sender,
                "[SISTEM] Contactul are o cheie noua. Verifica din nou safety number-ul.",
                True,
            )

        if self.current_partner == sender:
            self.update_ui_from_thread(self.refresh_verification_status, sender)

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg or not self.current_partner:
            return
            
        if not self.session_store.has_session(self.current_partner):
            self.save_and_display_message(self.current_partner, "[EROARE] Sesiunea E2EE nu este inca stabilita!", True)
            return

        aes_key = self.session_store.get_session_key(self.current_partner)
        if aes_key is None:
            self.save_and_display_message(self.current_partner, "[EROARE] Cheie de sesiune indisponibila.", True)
            return
        enc_data = encrypt_message(aes_key, msg)
        
        req = build_route(self.current_partner, PAYLOAD_MSG + enc_data)
        self.client_socket.sendall(req)
        
        self.save_and_display_message(self.current_partner, f"Tu: {msg}")
        self.msg_entry.delete(0, 'end')

    def update_ui_from_thread(self, func, *args):
        self.after(0, func, *args)

    # --- LOGICA DE RETEA ---
    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                    
                server_msg = parse_server_message(data)
                if server_msg is not None:
                    if server_msg.startswith("LINK_CODE:"):
                        link_code = server_msg.split(":", 1)[1]
                        messagebox.showinfo("Cod link device", f"Codul tau de link este:\n\n{link_code}")
                        self.save_and_display_message(
                            self.username,
                            f"[SISTEM] Cod link device generat: {link_code}",
                            True,
                        )
                        continue
                    if server_msg.startswith("LINK_OK:"):
                        account_id = server_msg.split(":", 1)[1]
                        if account_id:
                            self.profile = self.profile_store.update_account_link(account_id, account_mode="linked")
                        self.save_and_display_message(
                            self.username,
                            "[SISTEM] Device link-uit cu succes la cont. Relogin recomandat.",
                            True,
                        )
                        messagebox.showinfo("Link device", "Device link-uit cu succes la cont.")
                        continue
                    if server_msg.startswith("LINK_PENDING:"):
                        self.save_and_display_message(self.username, f"[SISTEM] {server_msg.split(':', 1)[1]}", True)
                        continue
                    if server_msg.startswith("LINK_ERR:"):
                        err = server_msg.split(":", 1)[1]
                        messagebox.showerror("Link device", err)
                        continue
                    if server_msg.startswith("LINK_INFO:"):
                        info = server_msg.split(":", 1)[1]
                        self.save_and_display_message(self.username, f"[SISTEM] {info}", True)
                        continue
                    if server_msg.startswith("LINK_APPROVAL_REQUEST:"):
                        # LINK_APPROVAL_REQUEST:<approval_ref>:<target_device_id>:<code>
                        parts = server_msg.split(":", 3)
                        if len(parts) == 4:
                            approval_ref, target_device_id, code = parts[1], parts[2], parts[3]
                            self.pending_link_approvals[approval_ref] = {
                                "target_device_id": target_device_id,
                                "code": code,
                            }
                            approved = messagebox.askyesno(
                                "Aprobare link device",
                                (
                                    "Un device nou cere acces la contul tau.\n\n"
                                    f"Device ID: {target_device_id}\nCod: {code}\n\n"
                                    "Aprobi link-ul?"
                                ),
                            )
                            if approved:
                                approval_text = f"LINK_APPROVAL:{self.username}:{approval_ref}:{target_device_id}"
                                signature_b64 = sign_link_approval(self.my_private_key, approval_text)
                                cmd = f"LINK_APPROVE_SIG:{self.username}:{approval_ref}:{signature_b64}"
                                self.client_socket.sendall(cmd.encode("utf-8"))
                            else:
                                self.save_and_display_message(
                                    self.username,
                                    "[SISTEM] Cererea de link device a fost respinsa local.",
                                    True,
                                )
                        continue
                    if server_msg.startswith("LINK_APPROVED:"):
                        # LINK_APPROVED:<account_id>:<creator_identity_b64>:<owner_username>:<approval_ref>:<target_device_id>:<signature_b64>
                        parts = server_msg.split(":", 6)
                        if len(parts) == 7:
                            account_id, creator_identity_b64 = parts[1], parts[2]
                            owner_username, approval_ref, target_device_id, signature_b64 = parts[3], parts[4], parts[5], parts[6]
                            if target_device_id != self.profile.get("device_id", ""):
                                messagebox.showerror("Link device", "Aprobarea primita nu este pentru acest device.")
                                continue
                            approval_text = f"LINK_APPROVAL:{owner_username}:{approval_ref}:{target_device_id}"
                            try:
                                creator_identity_bytes = base64.b64decode(creator_identity_b64.encode("ascii"))
                            except Exception:
                                messagebox.showerror("Link device", "Cheie de aprobare invalida.")
                                continue
                            if not verify_link_approval(creator_identity_bytes, approval_text, signature_b64):
                                messagebox.showerror("Link device", "Semnatura aprobarii nu este valida.")
                                continue
                            if account_id:
                                self.profile = self.profile_store.update_account_link(account_id, account_mode="linked")
                            self.save_and_display_message(
                                self.username,
                                "[SISTEM] Device link-uit cu succes dupa aprobare semnata.",
                                True,
                            )
                            messagebox.showinfo("Link device", "Device link-uit cu aprobare criptografica.")
                        continue
                    msg = server_msg
                    print(f"[SERVER]: {msg}")
                    continue
                
                from_data = parse_from(data)
                if from_data:
                    sender, payload = from_data

                    if payload.startswith(PAYLOAD_PUBKEY):
                        peer_pub_bytes = payload[len(PAYLOAD_PUBKEY):]
                        self.process_peer_key(sender, peer_pub_bytes)
                        aes_key = derive_aes_key(self.my_private_key, peer_pub_bytes)
                        self.session_store.set_session_key(sender, aes_key)
                        
                        reply = build_route(sender, PAYLOAD_PUBKEY_REPLY + self.my_public_bytes)
                        self.client_socket.sendall(reply)
                        
                        self.update_ui_from_thread(self.save_and_display_message, sender, f"[SISTEM] {sender} a initiat E2EE. Sesiune securizata.", True)
                    
                    elif payload.startswith(PAYLOAD_PUBKEY_REPLY):
                        peer_pub_bytes = payload[len(PAYLOAD_PUBKEY_REPLY):]
                        self.process_peer_key(sender, peer_pub_bytes)
                        aes_key = derive_aes_key(self.my_private_key, peer_pub_bytes)
                        self.session_store.set_session_key(sender, aes_key)
                        
                        self.update_ui_from_thread(self.save_and_display_message, sender, "[SISTEM] Negociere E2EE reusita! Canal securizat.", True)
                    
                    elif payload.startswith(PAYLOAD_MSG):
                        encrypted_msg = payload[len(PAYLOAD_MSG):]
                        sender_key = self.session_store.get_session_key(sender)
                        if sender_key is not None:
                            decrypted_text = decrypt_message(sender_key, encrypted_msg)
                            self.update_ui_from_thread(self.save_and_display_message, sender, f"{sender}: {decrypted_text}")

            except Exception as e:
                print(f"Deconectat din retea: {e}")
                break

    def on_closing(self):
        self.chat_archive_store.save_archive(self.session_store.export_messages())
        if self.client_socket:
            try:
                self.client_socket.close()
            except OSError as e:
                print(f"[WARN] Socket close failed: {e}")
        self.destroy()

if __name__ == "__main__":
    app = SecureChatApp()
    app.mainloop()