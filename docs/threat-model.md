# Threat model

| Threat | Primary mitigations | Residual risk |
|---|---|---|
| Stolen MCP bearer | localhost bind, private tunnel, root-only env, audit | tunnel/workstation compromise can read diagnostics |
| Malicious/mistaken prompt | no mutating tools, annotations, allowlists, bounds | non-sudo shell can read public files/use network |
| Command/host/name injection | fixed inventory addresses, exact allowlists, fixed root argv | unprivileged shell intentionally interprets its command |
| Secret-bearing output | recursive redaction, limits, no raw command audit | unknown encodings/formats can evade patterns |
| Diagnostic account compromise | no sudo/privileged groups, forced command, no TTY/forwarding | world-readable data and bounded resource/network use |
| Gateway/SSH-key compromise | dedicated source-restricted key, strict known hosts, mode 0600 | gateway root compromise reaches diagnostic accounts |
| Docker socket escalation | socket never exposed; diag user not in Docker group | root probe itself can read Docker state |
| Journal secret leakage | fixed units/windows/lines plus redaction | application secrets may use unrecognised shapes |
| Replay | SSH transport integrity, bearer comparison, request IDs, audit | bearer HTTP calls are not nonce-bound inside tunnel |
| Denial of service | timeout/output/process/file/concurrency limits | repeated allowed calls consume bounded resources |
| NAS unavailable | installed observer wheel/venv and config on local disk, NFS status tool | Docker applications may still fail by design |
| Release artifact substitution | exact semantic version, immutable URL, local/remote SHA-256 verification | compromised release account can still publish malicious bytes if the fleet pin is also reviewed incorrectly |
| Repository boundary erosion | CI rejects observer Python paths; no Git/filesystem link or editable install | documentation can still become stale across releases |
| One Pi offline | concurrent collection degrades per host/operation | no autonomous repair; operator action required |
| Forged/duplicate telemetry | stable unique client/topic/sensor IDs, two publications, HA registry/state/collision checks | MQTT credential theft can publish plausible data |

The design intentionally avoids sudo, Docker/journal groups, public MCP, arbitrary
root reads/shell, Docker exec, mutation APIs, and autonomous remediation. These are
security boundaries, not deferred convenience features.
