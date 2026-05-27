# Device Migration and Backup (v1)

SecureChat now supports encrypted local backups for:

- account profile metadata (`account_id`, `device_id`, mode, optional linked identifiers)
- identity private key + trust store
- local chat archive

## Backup Format

- File extension: `.scbackup`
- Envelope: JSON with KDF + nonce + ciphertext
- Encryption: AES-GCM
- Key derivation: PBKDF2-SHA256 (200k iterations)
- User secret: passphrase provided at export/import time

## Recovery Flow

1. Install app on new device.
2. Import `.scbackup` with passphrase.
3. App restores profile, identity, trust, and local archive.
4. Active sessions are reset and re-handshake is required.

## Important Limits (Current)

- This is user-managed backup; no cloud backup orchestration yet.
- No automatic multi-device key sync.
- If passphrase is weak or leaked, backup confidentiality is compromised.

## Next Upgrade Path

- Add optional recovery key (random 24-word secret) for stronger recovery.
- Add secure cloud-encrypted backup (client-side encrypted only).
- Strengthen current multi-device linking with:
  - explicit primary-device approval dialog
  - signed device-add events
  - per-device trust visualization in UI.
