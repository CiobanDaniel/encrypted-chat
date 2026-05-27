# SecureChat E2EE - Proiect de Criptare și Mesagerie

Acesta este un sistem de chat client-server care implementează **Criptare End-to-End (E2EE)** reală. Proiectul demonstrează utilizarea conceptelor avansate de securitate cibernetică, rutarea pachetelor într-o rețea și dezvoltarea unei interfețe grafice moderne în Python.

## Funcționalități Principale

* **Securitate Zero-Knowledge (pe server):** Serverul rutează doar pachete binare ilizibile. Nu are acces la cheile de decriptare și nu poate citi mesajele utilizatorilor.
* **Schimb Securizat de Chei (ECDH):** Cheile secrete sunt negociate dinamic la începutul fiecărei conversații folosind curbe eliptice (Elliptic-Curve Diffie-Hellman), prevenind atacurile de tip Man-in-the-Middle sau necesitatea de a stoca chei hardcodate.
* **Criptare Simetrică Autentificată (AES-GCM):** Mesajele sunt criptate cu AES-256-GCM, algoritm care asigură atât confidențialitatea, cât și integritatea datelor (previne alterarea mesajelor pe traseu).
* **Arhitectură Multi-Sesiune:** Un singur client poate gestiona simultan conversații securizate cu mai mulți parteneri, având o cheie unică AES generată pentru fiecare canal de comunicare în parte.
* **Interfață Grafică Modernă:** Construită cu `CustomTkinter`, oferă un design Dark Mode, suport pentru tab-uri (conversații active) și notificări vizuale pentru mesajele noi.

## Tehnologii Utilizate

* **Limbaj:** Python 3.10+
* **Rețelistică:** Modulul standard `socket` (TCP/IP) și `threading` pentru programare asincronă non-blocantă.
* **Criptografie:** Biblioteca `cryptography`
  * Algoritm Asimetric: `SECP384R1` (ECDH) pentru negocierea secretului comun.
  * Derivare Chei: `HKDF` (cu SHA256) pentru transformarea secretului comun într-o cheie puternică de 32 bytes.
  * Algoritm Simetric: `AES-GCM` cu un Nonce (Number Used Once) de 12 bytes generat aleatoriu per mesaj.
* **Interfață (UI):** Biblioteca `customtkinter`.

## Structura Proiectului

```text
chat-criptat-proiect/
│
├── server/
│   └── server.py           # Router-ul central (nu criptează/decriptează nimic)
│
├── client/
│   ├── client.py           # Interfața grafică și logica de rețea
│   ├── crypto_utils.py     # Modul izolat pentru criptare și safety number
│   ├── backup_utils.py     # Export/import backup criptat
│   ├── chat_archive_store.py # Persistență locală pentru istoric conversații
│   ├── identity_store.py   # Persistență pentru cheia de identitate și trust store
│   ├── profile_store.py    # Profil local (account_id, device_id, mod cont)
│   └── session_store.py    # Stare sesiuni/mesaje separată de UI
│
├── shared/
│   ├── config.py           # Configurații comune (IP, PORT, BUFFER_SIZE)
│   └── protocol.py         # Helpere comune pentru protocolul de transport
│
├── docs/
│   ├── threat-model.md     # Modelul de amenințări (v1)
│   ├── protocol-v1.md      # Specificația protocolului și pașii următori
│   ├── account-identity-model.md # Model pentru cont anonim + phone/email opțional
│   ├── device-migration-and-backup.md # Strategia de backup și migrare device
│   ├── deployment-separation.md # Cum rulezi server/client pe mașini diferite
│   └── hosting-options.md  # Opțiuni de hosting pentru lansare publică
│
├── deploy/
│   ├── haproxy/
│   │   └── haproxy.cfg      # Proxy TCP + limits de conexiune
│   ├── fail2ban/
│   │   ├── filter.d/securechat-haproxy.conf
│   │   └── jail.d/securechat.local
│   ├── scripts/
│   │   ├── ufw-harden.sh    # Script hardening firewall pentru VPS
│   │   └── healthcheck-tcp.sh # Health check simplu endpoint TCP
│   └── systemd/
│       └── securechat-server.service # Unit file pentru Linux servers
│
├── docker-compose.yml      # Deploy rapid server prin Docker Compose
├── docker-compose.prod.yml # Stack production: proxy + server intern
├── .env.example            # Variabile de mediu pentru server/client
├── .github/workflows/      # CI/CD: publish image, deploy VPS, uptime check
│
├── requirements.txt        # Dependințele proiectului
└── README.md               # Documentația curentă
```

## Ghid de Instalare și Rulare

### 1. Clonarea proiectului și pregătirea mediului
Este recomandat să folosiți un mediu virtual (Virtual Environment) pentru a instala dependințele.

```bash
# Clonează repository-ul
git clone https://github.com/CiobanDaniel/encrypted-chat.git
cd encrypted-chat

# Creează și activează mediul virtual (Windows)
python -m venv venv
venv\Scripts\activate

# (Pentru macOS/Linux, folosește: source venv/bin/activate)

# Instalează bibliotecile necesare
pip install -r requirements.txt
```

### 2. Pornirea Serverului
Serverul trebuie pornit primul pentru a accepta conexiunile.
```bash
python server/server.py
```
*(Pentru oprirea serverului folosiți combinația `Ctrl+C` în terminal).*

> Pentru deployment separat (server remote + client local), vezi `docs/deployment-separation.md`.

### 2.1 Pornire Server cu Docker Compose (opțional, recomandat pentru hosting)
```bash
# Copiază fișierul de env și ajustează valorile
cp .env.example .env

# Construiește și pornește serverul în background
docker compose up -d --build

# Verifică log-urile
docker compose logs -f securechat-server
```

### 2.1.1 Pornire stack production (HAProxy + server)
```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f securechat-proxy
```

### 2.1.2 Hardening rapid pe VPS (UFW)
```bash
chmod +x deploy/scripts/ufw-harden.sh
SECURECHAT_PUBLIC_PORT=65432 ./deploy/scripts/ufw-harden.sh
```

### 2.2 Pornire Server ca serviciu Linux (systemd)
1. Copiază repo-ul pe server (ex: `/opt/securechat`).
2. Copiază `deploy/systemd/securechat-server.service` în `/etc/systemd/system/`.
3. Creează `/etc/securechat/server.env` cu variabilele din `.env.example`.
4. Rulează:
```bash
sudo systemctl daemon-reload
sudo systemctl enable securechat-server
sudo systemctl start securechat-server
sudo systemctl status securechat-server
```

### 3. Pornirea Clienților
Deschideți terminale separate (cu mediul virtual activat) pentru a lansa instanțe de clienți:
```bash
python client/client.py
```

## Mod de Utilizare (Fluxul aplicației)

1. **Autentificare:** La pornirea clientului, introduceți un nume de utilizator unic (ex: *Alice*). Acest nume este trimis serverului pentru a vă înregistra în tabelul de rutare.
2. **Inițierea unei conversații:** Conectați un al doilea client (ex: *Bob*). În interfața lui Alice, căutați numele *Bob* și apăsați "Deschide Chat".
3. **Negocierea E2EE:** În fundal, se execută automat un "Handshake":
   * Alice trimite cheia ei publică prin server către Bob.
   * Bob o primește, își calculează cheia secretă, și îi răspunde lui Alice cu cheia lui publică.
   * Alice o primește și își calculează cheia secretă (care acum este matematic identică cu a lui Bob).
4. **Comunicarea:** Odată afișat mesajul de sistem "Canal securizat", puteți schimba mesaje. Serverul va afișa în terminalul său doar pachetele rulate sub forma unor șiruri de octeți indescifrabile.

---
*Proiect realizat pentru disciplina de Criptografie și securitate informațională.*