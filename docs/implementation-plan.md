# Implementation plan

This checklist maps the bounded delivery directly to the governing
specification. Production mutation is intentionally outside the implementation
phase until check-mode output is reviewed and separately approved.

## Phase 1 — safety and read-only discovery

- [x] Add the permanent repository operating contract (`AGENTS.md`).
- [x] Add this specification-linked checklist.
- [x] Test read-only SSH connectivity to all four managed hosts and BenNAS.
- [x] Capture OS, architecture, hostname, mounts, systemd, Docker, Code Tunnel,
  reporter, watchdog, cron, network, HA, and MQTT facts without exposing secrets.
- [x] Compare both existing Pi reporter installations and both watchdog installs.
- [x] Record evidence and assumptions in `reports/current-state.*` and docs.

## Phase 2 — declarative fleet foundation

- [x] Build YAML inventory and required inheritance groups/host variables.
- [x] Add safe defaults, vault examples, Ansible configuration, dependencies,
  lint configuration, Python packaging, Make targets, and secret exclusions.
- [x] Implement identity, NFS/Docker ordering, Code Tunnel, Pi telemetry,
  configuration backup, and existing OTBR watchdog roles.
- [x] Include timestamped adoption backups, validations, guarded handlers, and
  check-mode support.
- [x] Implement discover, audit, bootstrap, adopt, enrol, verify, backup, and
  observer playbooks.

## Phase 3 — observer and MCP

- [x] Implement the constrained `chatgpt-diag` account and forced-command runner.
- [x] Implement the typed Unix-socket read-only probe agent and `hlctl` client.
- [x] Implement inventory-derived operation/service/container allowlists,
  fixed argv, bounds, redaction, audit, and structured errors.
- [x] Implement the BenBeast SSH gateway and localhost-only Streamable HTTP MCP
  server with all required tools and correct safety annotations.
- [x] Implement correlated incident profiles and HA/MQTT verification adapters.
- [x] Add project-scoped MCP connection example and private-tunnel docs.

## Phase 4 — operations and verification

- [x] Implement enrolment, audit, verification, and incident scripts.
- [x] Generate telemetry verification JSON/Markdown without credentials.
- [x] Document architecture, discovery, onboarding, retrofit, backups, security,
  operations, rollback, assumptions, threat model, and exact phased rollout.
- [x] Cover required observer and Ansible policy cases with automated tests.
- [x] Run unit tests, ruff, mypy, yamllint, ansible-lint, all playbook syntax
  checks, shellcheck (when installed), and tracked-secret scanning via `make test`.
- [x] Run `playbooks/adopt.yml --check --diff` only after local tests pass.
- [x] Capture exact local-test and reachable-host check-mode results. The three
  Pis passed; BenBeast is explicitly recorded as become-credential blocked.

## Phase 5 — approval-gated production rollout (not automatic)

- [ ] Present check-mode changes and obtain explicit approval per phase/host.
- [ ] ZigbeePi observer access; verify Zigbee/Z-Wave remain healthy.
- [ ] ZigbeePi telemetry and Code Tunnel; verify MQTT and fresh HA state.
- [ ] LoungeOTBR telemetry/observer; verify OTBR remains healthy.
- [ ] Pironman adoption; verify OTBR, Matter, Pi-hole, and Unbound.
- [ ] BenBeast observer gateway; verify Home Assistant.
- [ ] Install NFS/systemd consistency files without remount/restart.
- [ ] Separately approve later one-host-at-a-time boot-order validation.

## Completion evidence

- [x] Separate implemented repository state, verified live facts, ready-but-not-
  applied changes, and blocked work in the final report.
- [x] Include full tree, assumptions, exact tests/results, host reachability,
  missing secrets, rollout, risks, and exact rollback procedures.
- [x] Never report a host, service, telemetry chain, or idempotence as verified
  without the corresponding fresh evidence.
