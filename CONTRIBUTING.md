# Contributing Guide

## Principles

- Prefer small pull requests.
- Keep security-sensitive changes isolated and well documented.
- Never commit secrets, tokens, private keys, or production credentials.

## Local Checks

Run before opening a PR:

```bash
python -m compileall .
```

## Pull Request Requirements

- Fill in the PR template completely.
- Add test/verification notes.
- Call out security impact explicitly.
- Update docs when behavior or deployment changes.

## Security-Sensitive Areas

Changes touching these paths require extra care and review:

- `shared/protocol.py`
- `client/crypto_utils.py`
- `client/identity_store.py`
- `server/server.py`
- `deploy/`
- `.github/workflows/`

## Commit Hygiene

- Keep commit messages concise and descriptive.
- Prefer one logical change per commit where possible.
