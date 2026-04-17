# client/client.py
import socket
import threading
import sys
import os
import customtkinter as ctk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import HOST, PORT, BUFFER_SIZE
from crypto_utils import generate_keypair, derive_aes_key, encrypt_message, decrypt_message

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
        
        # Dictionare pentru managementul sesiunilor si interfetei
        self.active_sessions = {}  # { "Bob": <cheie_aes> }
        self.messages = {}         # { "Bob": ["Tu: salut", "Bob: hello"] }
        self.chat_buttons = {}     # { "Bob": <obiect_buton> }
        
        self.current_partner = None

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
            self.client_socket.connect((HOST, PORT))
        except Exception:
            self.error_label.configure(text="Eroare: Server offline!")
            return

        self.client_socket.sendall(f"REGISTER:{self.username}".encode('utf-8'))
        self.my_private_key, self.my_public_bytes = generate_keypair()

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
        
        # Lista de conversatii active (Tab-uri)
        ctk.CTkLabel(self.sidebar_frame, text="Conversatii Active:", text_color="gray").pack(pady=(15, 0))
        self.contacts_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.contacts_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- MAIN CHAT AREA ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Nicio conversatie deschisa", font=("Arial", 14))
        self.status_label.pack(pady=10)

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
            self.messages[target_user] = []
            btn = ctk.CTkButton(self.contacts_frame, text=target_user, fg_color="transparent", 
                                hover_color="#2c2c2c", anchor="w",
                                command=lambda u=target_user: self.switch_chat(u))
            btn.pack(fill="x", pady=2)
            self.chat_buttons[target_user] = btn

    def switch_chat(self, target_user):
        """Schimba contextul conversatiei catre utilizatorul selectat."""
        self.current_partner = target_user
        self.status_label.configure(text=f"Conversatie cu: {target_user}", text_color="#2FA572")
        
        # Resetam culoarea butonului (in caz ca era evidentiat pentru mesaj necitit)
        self.chat_buttons[target_user].configure(fg_color="#1f6aa5")

        # Reincarcam istoricul mesajelor pentru acest utilizator
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        for msg in self.messages[target_user]:
            self.chat_history.insert("end", msg + "\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    def save_and_display_message(self, user, message, is_system=False):
        """Salveaza mesajul in istoric si il afiseaza daca acel chat e deschis curent."""
        # Ne asiguram ca utilizatorul are tab
        self.add_contact_tab(user)
        
        self.messages[user].append(message)

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
        
        if target not in self.active_sessions:
            self.save_and_display_message(target, "[SISTEM] Cheia publica a fost trimisa. Asteptam negocierea...", True)
            req = f"ROUTE:{target}:".encode('utf-8') + b"PUBKEY:" + self.my_public_bytes
            self.client_socket.sendall(req)

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg or not self.current_partner:
            return
            
        if self.current_partner not in self.active_sessions:
            self.save_and_display_message(self.current_partner, "[EROARE] Sesiunea E2EE nu este inca stabilita!", True)
            return

        aes_key = self.active_sessions[self.current_partner]
        enc_data = encrypt_message(aes_key, msg)
        
        req = f"ROUTE:{self.current_partner}:".encode('utf-8') + b"MSG:" + enc_data
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
                    
                if data.startswith(b"SERVER:"):
                    msg = data[7:].decode('utf-8')
                    print(f"[SERVER]: {msg}")
                    continue
                
                if data.startswith(b"FROM:"):
                    parts = data.split(b":", 2)
                    if len(parts) < 3:
                        continue
                    
                    sender = parts[1].decode('utf-8')
                    payload = parts[2]
                    
                    if payload.startswith(b"PUBKEY:"):
                        peer_pub_bytes = payload[7:]
                        aes_key = derive_aes_key(self.my_private_key, peer_pub_bytes)
                        self.active_sessions[sender] = aes_key
                        
                        reply = f"ROUTE:{sender}:".encode('utf-8') + b"PUBKEY_REPLY:" + self.my_public_bytes
                        self.client_socket.sendall(reply)
                        
                        self.update_ui_from_thread(self.save_and_display_message, sender, f"[SISTEM] {sender} a initiat E2EE. Sesiune securizata.", True)
                    
                    elif payload.startswith(b"PUBKEY_REPLY:"):
                        peer_pub_bytes = payload[13:]
                        aes_key = derive_aes_key(self.my_private_key, peer_pub_bytes)
                        self.active_sessions[sender] = aes_key
                        
                        self.update_ui_from_thread(self.save_and_display_message, sender, "[SISTEM] Negociere E2EE reusita! Canal securizat.", True)
                    
                    elif payload.startswith(b"MSG:"):
                        encrypted_msg = payload[4:]
                        if sender in self.active_sessions:
                            decrypted_text = decrypt_message(self.active_sessions[sender], encrypted_msg)
                            self.update_ui_from_thread(self.save_and_display_message, sender, f"{sender}: {decrypted_text}")

            except Exception as e:
                print(f"Deconectat din retea: {e}")
                break

    def on_closing(self):
        if self.client_socket:
            try: 
                self.client_socket.close()
            except Exception: 
                pass
        self.destroy()

if __name__ == "__main__":
    app = SecureChatApp()
    app.mainloop()