# Security and credential handling

Commit no credentials. Copy the placeholder Vault file to ignored `vault.yml`,
replace values locally, and encrypt it with `ansible-vault`. Do not pass secrets on
the command line, print decrypted variables, or include them in reports/diffs.

Observer runtime JSON contains host policy and endpoints but no tokens, passwords,
or private keys. Gateway secrets are written from Vault into a root-only environment
file and SSH directory. The diagnostic account has no sudo or privileged groups;
its key is source-restricted and forced through the released bounded runner. MCP is
localhost-only. See `docs/observer-security.md` and `docs/threat-model.md` for the
deployment boundary and the observer repository for application-level controls.

Artifact integrity is mandatory: use the exact release URL and SHA-256, review pin
changes, and never substitute a local artifact unless its controller-side checksum
matches. Missing credentials block live application but do not justify weakening
authentication or committing a secret.

Private-release authorization headers, when direct managed-host download is used,
belong only in encrypted `vault_observer_release_headers` and are suppressed by the
download task. Controller-side authenticated download plus checked local copy is
the preferred rollout path.
