# Protocol v1 Draft

This is a transitional protocol spec for the current codebase. It standardizes packet framing and defines a migration path toward stronger authenticated E2EE.

## Current Transport Frame

- `REGISTER:<username>`
- `REGISTER_JSON:<json_payload>`
- `LINK_CREATE:<username>:<device_id>`
- `LINK_CONSUME:<username>:<code>:<new_device_id>`
- `LINK_APPROVE_SIG:<username>:<link_token>:<signature_b64>`
- `ROUTE:<target_username>:<payload_bytes>`
- `FROM:<sender_username>:<payload_bytes>`
- `SERVER:<message>`

`REGISTER_JSON` is currently used for local account/device abstraction and optional linked identifiers metadata.
`LINK_CREATE` and `LINK_CONSUME` are current server-assisted primitives for multi-device account linking.
`LINK_APPROVE_SIG` finalizes linking only after primary-device signed approval.

## Identity and Discovery Direction

- Transport `REGISTER` should evolve from username-only to device-aware registration:
  - account id (or anonymous id)
  - device id
  - identity public key
- Discovery identifiers (phone/email) should be optional and handled outside message encryption flow.
- Verified phone/email must not be treated as equivalent to safety-number verification.

## Current E2EE Payload Types

- `PUBKEY:<pem_public_key>`
- `PUBKEY_REPLY:<pem_public_key>`
- `MSG:<nonce_plus_ciphertext>`

## Session Establishment (Current)

1. Initiator sends `PUBKEY`.
2. Receiver derives shared key via ECDH + HKDF, stores session key, replies with `PUBKEY_REPLY`.
3. Initiator derives session key after `PUBKEY_REPLY`.
4. Both sides exchange `MSG` payloads encrypted with AES-GCM.

## Known Weaknesses

- No authenticated identity binding for public keys (MITM possible).
- No replay protection metadata.
- No ratcheting for post-compromise security.
- Session/key state is in-memory only.

## Near-Term Protocol Upgrades

### 1) Identity Layer

- Add persistent device identity keypair:
  - `IDENTITY_KEY_PUB` published to server profile.
  - Private key stored locally in secure storage.

### 2) Prekey Bundle

- Add endpoint to fetch:
  - identity public key
  - signed prekey
  - one-time prekey (optional for each session bootstrap)

### 3) Authenticated Handshake

- Replace `PUBKEY`/`PUBKEY_REPLY` with `INIT` message containing ephemeral key and references to prekeys.
- Include signature validation to bind prekeys to identity key.

### 4) Message Envelope Structure

- Standardize encrypted payload as:
  - protocol version
  - session id
  - sender device id
  - message counter
  - ciphertext

Counters and session identifiers should be authenticated as AAD.

## Implementation Notes

- Parsing/building of wire frames now lives in `shared/protocol.py`.
- In-memory session/message state now lives in `client/session_store.py`.
- UI should not perform direct wire framing or ad-hoc byte parsing.
