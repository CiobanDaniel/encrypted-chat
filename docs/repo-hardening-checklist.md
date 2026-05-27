# Repository Hardening Checklist

Some controls are configured in-repo (files/workflows), while branch protection must be enabled in GitHub settings.

## In-repo controls added

- `CODEOWNERS` for sensitive paths
- PR template with security/testing/rollback sections
- `SECURITY.md` private disclosure guidance
- `CONTRIBUTING.md` rules for contributors
- `ci-security.yml` workflow (compile, bandit, pip-audit, gitleaks)
- GitHub workflows set to least-privilege permissions where possible

## Required GitHub settings (manual)

For branch `main`:

1. Require a pull request before merging.
2. Require approvals (1-2 reviewers).
3. Dismiss stale approvals when new commits are pushed.
4. Require status checks to pass:
   - `CI Security Checks / quality-and-security`
5. Require conversation resolution before merge.
6. Restrict who can push to matching branches.
7. Disable force pushes.
8. Disable branch deletion.

Repository security settings:

1. Enable Dependabot alerts and updates.
2. Enable secret scanning and push protection.
3. Keep Actions workflow permissions default as `Read repository contents`.

## Optional CLI command (if you use GitHub CLI)

```bash
gh api \
  -X PUT \
  repos/<owner>/<repo>/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks[strict]=true \
  -f required_pull_request_reviews[dismiss_stale_reviews]=true \
  -F required_pull_request_reviews[required_approving_review_count]=1 \
  -f enforce_admins=true \
  -f restrictions=
```

Use this carefully and adapt for your team/repo policy.
