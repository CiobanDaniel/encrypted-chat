# Client/Server Separation Deployment Guide

The project now supports independent runtime configuration for client and server.

## 1) Server deployment config

Set these env vars on the server host:

- `SECURECHAT_SERVER_BIND_HOST` (default `0.0.0.0`)
- `SECURECHAT_SERVER_BIND_PORT` (default `65432`)

Example (Linux):

```bash
export SECURECHAT_SERVER_BIND_HOST=0.0.0.0
export SECURECHAT_SERVER_BIND_PORT=65432
python server/server.py
```

## 2) Client config (remote DNS/IP)

Set these env vars on each client device:

- `SECURECHAT_SERVER_HOST` (example: `chat.yourdomain.com`)
- `SECURECHAT_SERVER_PORT` (example: `65432`)

Example:

```bash
export SECURECHAT_SERVER_HOST=chat.yourdomain.com
export SECURECHAT_SERVER_PORT=65432
python client/client.py
```

## 3) Hosting checklist

- Open inbound TCP port (`SECURECHAT_SERVER_BIND_PORT`) in firewall.
- Point DNS A/AAAA record to your server public IP.
- Keep server process running via system service (systemd / pm2 / supervisor).
- Add TLS termination or VPN tunnel in production (current transport is plain TCP).

## 4) Security note

Server and client can run on different machines today.  
E2EE payload remains encrypted end-to-end, but transport metadata is still visible to the server and network path.
