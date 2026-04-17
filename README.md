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
│   └── crypto_utils.py     # Modul izolat pentru generarea și derivarea cheilor
│
├── shared/
│   └── config.py           # Configurații comune (IP, PORT, BUFFER_SIZE)
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