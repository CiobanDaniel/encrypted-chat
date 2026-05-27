# Threat Model (v1)

This document defines what SecureChat v1 is trying to protect, and what it does not protect yet.

## Security Goals

- Message confidentiality: only participants can read message content.
- Message integrity: ciphertext tampering is detected.
- Server zero-knowledge for content: routing service cannot decrypt payloads.
- Forward secrecy (target for next protocol version): compromise of long-term keys should not reveal old message history.

## Trust Boundaries

- **Client devices:** trusted for plaintext handling and key operations.
- **Transport/server:** untrusted for content confidentiality and metadata minimization.
- **Network path:** untrusted (active attacker possible).

## Primary Threats

- Passive network capture.
- Active man-in-the-middle (MITM) during initial key exchange.
- Malicious or compromised server relaying manipulated handshake payloads.
- Local malware or physical access to unlocked client machine.
- Replay or reordering of encrypted packets.

## Out of Scope (v1)

- Global metadata resistance (who talks to whom, when, and how often).
- Nation-state traffic analysis resistance.
- Multi-device sync security.
- Perfect deniability guarantees.
- Recovery from fully compromised endpoints.

## Security Requirements for Upcoming Milestones

1. Persist long-term identity keypair per device.
2. Add verifiable identity UX (safety number / QR verification).
3. Replace ad-hoc handshake with a standard pattern (X3DH-like bootstrap + ratchet).
4. Add replay protection using counters and per-session state.
5. Store local key material securely (OS-backed keystore where possible).

## Assumptions

- Cryptographic primitives from maintained libraries are correctly implemented.
- Random number generation source is secure on target OS.
- Users can verify contact identity out-of-band when prompted.
