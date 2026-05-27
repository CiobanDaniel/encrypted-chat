# Account and Identity Model (Optional Phone/Email)

This document defines how SecureChat can support two onboarding modes:

- **Anonymous mode:** no phone/email required.
- **Linked mode:** optional phone number or email linked to profile.

The E2EE identity must remain the same in both modes: device keys and verified safety numbers.

## Core Principles

- Phone/email is for discoverability and recovery UX, not for message decryption.
- The server must never hold private identity keys.
- One user may have multiple devices, each with its own device key.
- Contacts are trusted by cryptographic key verification, not by phone/email alone.

## Identity Objects

- **Account ID:** random stable identifier (`acct_...`) created server-side.
- **Profile handle:** optional public name/username.
- **Reachability claims (optional):**
  - `email_hash` (salted/peppered hash)
  - `phone_hash` (normalized E.164 then hashed)
- **Device identity key:** long-term public key per device.

## Onboarding Flows

### 1) Anonymous Mode

1. Create account with random ID and optional nickname.
2. Register device identity key.
3. Start chatting by username/share code/QR contact exchange.

### 2) Linked Mode (Optional)

1. Create account as above.
2. User can add phone/email later.
3. Verification (OTP/email link) is optional policy per deployment.
4. Contacts can discover user through hashed lookup (never plaintext directory export).

## Safety Recommendations

- Do not allow silent key replacement for an existing device.
- If device key changes, mark contact as unverified and show hard warning.
- Rate-limit identifier lookup and signup to reduce abuse.
- Keep legal/abuse handling at metadata/report level; do not weaken E2EE for content scanning.

## Suggested API Shape (Future)

- `POST /accounts/create` -> returns `account_id`
- `POST /accounts/link-identifier` -> `{type: phone|email, value, verification_code?}`
- `POST /devices/register` -> `{account_id, device_pub_key, device_name}`
- `GET /prekeys/bundle/{account_or_username}`
- `POST /directory/lookup` -> hashed identifiers only

## Threat Notes

- Optional phone/email adds PII risk and account-takeover surface.
- Anonymous mode reduces PII but increases abuse potential.
- Support both modes by separating:
  - **Identity for trust:** cryptographic keys
  - **Identity for discovery:** optional identifiers
