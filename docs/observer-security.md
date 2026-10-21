> Publication copy: deployment addresses and domains below are examples; restore private inputs before use.

# Observer security

Application-level enforcement and its threat model live in the independent
`homelab-observer` release. Fleet owns the deployment half of the boundary: it
accepts only the exact pinned wheel SHA-256, installs into a dedicated local-disk
venv, generates schema-v1 allowlists from inventory, and keeps secrets outside the
runtime JSON. No observer source or standalone dependency list is deployed by an
Ansible role.

`chatgpt-diag` is password-locked, has no sudo, Docker, journal, or adm membership,
and owns only `/var/lib/chatgpt-diag/scratch`. Its sole authorized key is restricted
to source `192.0.2.2`, uses OpenSSH `restrict`, and forces the local runner.
The sshd Match block independently disables TTY, agent/X11/TCP forwarding, tunnels,
keyboard/password auth, and gateways.

The forced runner sanitises environment and cwd; closes stdin; rejects empty and
direct privilege-changing commands; caps timeout at 60 seconds and total output at
512 KiB; sets core/file/process limits; starts a process group; and kills the group
after success or timeout so redirected background jobs cannot survive. Audit logs
contain requester, host, duration, result, timeout, and command SHA-256—not the raw
command.

Keyword rejection is defence in depth, not the privilege boundary. Arbitrary
non-sudo commands can still read world-readable files, consume bounded resources,
and make network requests permitted to that user. Clients must treat this tool as
approval-requiring.

The root agent listens only on mode-0660 `/run/homelab-observer/agent.sock`. It
accepts fixed operation names, validates service/container names against generated
inventory, uses fixed argv with `shell=False`, applies time/line/output bounds,
redacts responses, and returns structured errors. It never exposes a TCP or Docker
socket and never implements exec, restart, write, package, reboot, or arbitrary
file/journal access.

The MCP listener remains `127.0.0.1` by generated policy. The bearer token, HA
token, MQTT credentials, SSH private key, and known-host pins come only from
encrypted Vault variables and root-readable files. Release provenance does not
replace those controls; both artifact integrity and runtime least privilege are
required.
