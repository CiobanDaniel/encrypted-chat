#!/usr/bin/env bash
set -euo pipefail

# Harden a Linux VPS with UFW for SecureChat.
# Usage:
#   SECURECHAT_PUBLIC_PORT=65432 ./deploy/scripts/ufw-harden.sh

PUBLIC_PORT="${SECURECHAT_PUBLIC_PORT:-65432}"
SSH_PORT="${SSH_PORT:-22}"

echo "[*] Installing UFW if missing..."
if ! command -v ufw >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ufw
fi

echo "[*] Resetting UFW rules..."
sudo ufw --force reset

echo "[*] Applying default policies..."
sudo ufw default deny incoming
sudo ufw default allow outgoing

echo "[*] Allowing SSH on port ${SSH_PORT}..."
sudo ufw allow "${SSH_PORT}/tcp"

echo "[*] Allowing SecureChat public port ${PUBLIC_PORT}..."
sudo ufw allow "${PUBLIC_PORT}/tcp"

echo "[*] Enabling UFW..."
sudo ufw --force enable
sudo ufw status verbose

echo "[+] Firewall hardening complete."
