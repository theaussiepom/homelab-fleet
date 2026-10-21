# homelab-fleet operating contract

This repository manages a production home-automation fleet. Existing working
services and live host state are the source of truth. Every contributor and
automation session must preserve the following contract.

## Scope

Implement only declarative Ansible adoption/enrolment, Code Tunnel, existing Pi
telemetry, telemetry verification, NFS-before-Docker ordering, the existing OTBR
watchdog, encrypted local-configuration backups, fleet audit/admission, and the
private read-only diagnostics/MCP system described by this repository.

This repository owns deployment policy, not the observer application. Observer
Python source, package metadata, and application tests belong only in the
independent `homelab-observer` repository. Consume observer solely as an exact
semantic version, immutable release URL, and SHA-256-verified wheel; never add a
submodule, subtree link, symlink, editable install, production Git clone, floating
branch install, or copied Python module.

Do not add OS reflashing, Kubernetes, Terraform, a dashboard, a monitoring or
MQTT migration, a Home Assistant/reporter/tunnel/watchdog replacement, bots,
autonomous remediation, a public control plane, Swarm redesign, broad Compose
normalisation, mass restart-policy changes, radio-network reconfiguration,
Home Assistant entity renames without a proven collision, direct `.storage`
edits, public MCP exposure, privileged arbitrary diagnostics, mutating MCP
tools, or NAS administration.

BenNAS is an external dependency. Check its connectivity only.

## Production safety gates

Read-only SSH discovery is allowed. Before changing a live host:

1. Complete read-only discovery.
2. Finish the relevant role.
3. Pass local tests, Ansible syntax checks, and lint.
4. Run the role/playbook with `--check --diff`.
5. Present the exact proposed live changes.
6. Obtain explicit human approval for live application.

Never perform any of the following without explicit approval: reboot,
shutdown, Docker daemon restart, `docker compose down`, container stop/restart/
update, production NFS mount/unmount, full OS upgrade, OS release upgrade,
destructive Git operation, backup deletion, or any Thread/Matter/Zigbee/Z-Wave
configuration change. Do not restart unrelated services. Never simulate an
OTBR hard failure in production.

All mutation safety variables default to false. No role may bypass them:

- `homelab_allow_service_restart`
- `homelab_allow_docker_restart`
- `homelab_allow_reboot`
- `homelab_allow_nfs_remount`
- `homelab_allow_otbr_restart`
- `homelab_retire_legacy_backup`

Create timestamped backups before replacing adopted managed files. Keep the
OTBR watchdog state file in place and never restore it from backup. Install NFS
boot changes without remounting NFS or restarting Docker; boot verification is
a later, separately approved, host-by-host maintenance procedure.

## Security and secrets

Never commit or print secrets. Use Ansible Vault variables/examples and
environment-provided credentials. Redact secrets from terminal output, diffs,
tests, generated reports, diagnostics, and final summaries.

`chatgpt-diag` has no sudo, Docker socket/group, journal/adm membership, password
login, interactive TTY, or production write access. Its SSH key is source-
restricted and forced through the bounded wrapper. Privileged inspection is
only through fixed, validated, read-only probe operations. Never add root shell,
arbitrary file/journal reads, Docker exec, service/container mutation, package
changes, reboot, or file writes to the probe or MCP API.

The MCP listener remains on localhost by default and must not gain a public
listener or reverse proxy. Host, service, and container inputs are inventory-
derived allowlists. Enforce time, output, process, and concurrency bounds,
redaction, and audit logging. Treat arbitrary non-sudo shell as risky and
approval-requiring even though it is unprivileged.

## Live-state preservation

- Preserve every host's own Code Tunnel identity and authentication state.
- Discover both existing Pi reporters before choosing a canonical version.
- Never invent MQTT/HA endpoints, credentials, topics, IDs, paths, or users.
- Preserve unique MQTT clients and Home Assistant device/entity unique IDs.
- Preserve OTBR datasets, device maps, restart policy, Matter roles, and the
  existing watchdog recovery semantics.
- Do not treat NAS-to-same-NAS copies as independent disaster recovery.
- Do not retire legacy backup cron until restic backup and check succeed and
  `homelab_retire_legacy_backup=true` is explicitly set.
- Keep the installed observer wheel/venv, generated configuration, mount helpers,
  and bootstrap code on local disk so they work while NFS is unavailable.

## Engineering rules

Use fully qualified Ansible modules, idempotent/check-mode-safe tasks, handlers
only for real changes, validation before activation, typed Python 3.11+, fixed
argv for privileged subprocesses, explicit bounds, structured errors/logging,
and shell scripts with `set -euo pipefail`, correct quoting, and no `eval`.

Changes to the observer pin must update version, release URL, and SHA-256 together,
pass the independent observer release gate, and validate the generated runtime
schema before any rollout. Never silently advance the supported schema version.

Use Australia/Sydney timestamps in human-readable reports. Record unresolved
facts and evidence-based assumptions in `docs/assumptions.md`. A missing secret
does not block repository implementation. Never claim live health, HA telemetry,
idempotence, or application success without direct evidence.
