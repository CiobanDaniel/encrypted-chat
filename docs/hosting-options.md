# Hosting Options for Public Usage

If you want users worldwide to connect to your server, you need a public host with a stable domain and open TCP port.

## Good first production options

- **VPS (Hetzner / DigitalOcean / Linode / Vultr):**
  - Best control/cost for an early-stage app.
  - Run Docker Compose or systemd directly.
- **Cloud VM (AWS EC2 / Azure VM / GCP Compute Engine):**
  - Similar to VPS, better ecosystem integrations.
- **Managed Kubernetes (AKS/EKS/GKE):**
  - Good only when you need autoscaling and ops maturity.
  - Overkill for first public release.

## Practical recommendation (your stage)

1. Start with one VPS (2 vCPU, 4 GB RAM).
2. Deploy `securechat-server` via Docker Compose.
3. Add domain `chat.yourdomain.com` -> VPS IP.
4. Open firewall for server TCP port.
5. Add monitoring + backups + log rotation.

## Before public launch

- Add TLS transport (or tunnel through a secure proxy/VPN).
- Add rate limiting and abuse controls.
- Add server auth and anti-enumeration protections.
- Add observability (uptime, errors, connection counts).

## Included production starter stack in this repo

- `docker-compose.prod.yml`:
  - `securechat-server` container (internal network only)
  - `securechat-proxy` (HAProxy TCP edge)
- `deploy/haproxy/haproxy.cfg`:
  - connection burst limit per source IP
  - TCP health checks
- `deploy/fail2ban/*`:
  - starter jail/filter templates for banning abusive IPs
- `.github/workflows/publish-server-image.yml`:
  - auto-build and publish server image to GHCR on `main`/tags
- `.github/workflows/deploy-vps.yml`:
  - deploys tagged release to VPS over SSH
- `.github/workflows/uptime-check.yml`:
  - checks TCP endpoint every 10 minutes (fails workflow if down)

## GitHub secrets needed for CI/CD

- `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_SSH_PORT`
- `SECURECHAT_HEALTH_HOST`, `SECURECHAT_HEALTH_PORT`
