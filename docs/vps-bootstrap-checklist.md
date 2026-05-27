# VPS Bootstrap Checklist (Ubuntu) - SecureChat

This is an end-to-end checklist from a fresh Ubuntu VPS to a running public SecureChat server.

## 0) Prerequisites

- Domain/subdomain ready (example: `chat.example.com`)
- Ubuntu 22.04+ VPS with public IP
- SSH access with sudo user

## 1) DNS setup

1. Create `A` record:
   - Name: `chat`
   - Value: `<VPS_PUBLIC_IP>`
2. Wait for propagation.
3. Verify:

```bash
nslookup chat.example.com
```

## 2) Initial server hardening

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git curl ca-certificates ufw fail2ban
```

Optional: disable password SSH and use keys only in `/etc/ssh/sshd_config`.

## 3) Install Docker + Compose plugin

```bash
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

Log out/in once so docker group applies.

## 4) Clone project

```bash
sudo mkdir -p /opt/securechat
sudo chown -R $USER:$USER /opt/securechat
cd /opt/securechat
git clone https://github.com/CiobanDaniel/encrypted-chat.git .
```

## 5) Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

- `SECURECHAT_SERVER_BIND_HOST=0.0.0.0`
- `SECURECHAT_SERVER_BIND_PORT=65432`
- `SECURECHAT_PUBLIC_PORT=65432`

## 6) Apply firewall rules

```bash
chmod +x deploy/scripts/ufw-harden.sh
SECURECHAT_PUBLIC_PORT=65432 ./deploy/scripts/ufw-harden.sh
```

Make sure SSH remains open (default script keeps port 22).

## 7) Launch production stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f securechat-proxy
```

## 8) Verify endpoint health

From local machine:

```bash
nc -vz chat.example.com 65432
```

From server:

```bash
chmod +x deploy/scripts/healthcheck-tcp.sh
./deploy/scripts/healthcheck-tcp.sh chat.example.com 65432
```

## 9) Client configuration

On each client machine:

- `SECURECHAT_SERVER_HOST=chat.example.com`
- `SECURECHAT_SERVER_PORT=65432`

Then run:

```bash
python client/client.py
```

## 10) GitHub Actions setup (optional but recommended)

Repository secrets:

- Deploy: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_SSH_PORT`
- Uptime: `SECURECHAT_HEALTH_HOST`, `SECURECHAT_HEALTH_PORT`

Then:

- Push to `main` -> image publishes to GHCR
- Push tag `vX.Y.Z` -> deploy workflow can deploy to VPS

## 11) Day-2 operations checklist

- Monitor `docker compose logs` daily
- Keep OS/packages updated
- Rotate and secure SSH keys
- Back up `/opt/securechat/.env` and any future persistent server data
- Plan TLS transport hardening before larger public rollout
