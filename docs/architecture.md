# Architecture

The control plane is this private Git repository plus Ansible. Inventory aliases
are canonical observer names even when Linux hostnames differ. Group membership
supplies mandatory roles: every managed host gets fleet identity, Code Tunnel,
diagnostic access, and the checksum-pinned observer wheel; every Pi additionally
gets the existing telemetry reporter and configuration-only backup. Only the two
OTBR hosts get the watchdog; only BenBeast gets the gateway service.

The repositories have a deliberately one-way dependency:

```text
homelab-observer repository
  test -> build wheel -> versioned private release
                           |
                           | version + immutable URL + SHA-256
                           v
homelab-fleet inventory -> runtime.json schema v1 -> managed hosts
                           |
                           +-> /opt/homelab-observer/venv
                           +-> /etc/homelab-observer
                           +-> /var/lib/homelab-observer
                           +-> /run/homelab-observer
```

Fleet never copies Python source, and observer never reads this checkout or
Ansible inventory. `runtime.json.j2` serialises canonical names, SSH destinations,
capabilities, service/container allowlists, unique telemetry identities, command
bounds, HA/MQTT endpoints, audit policy, gateway paths, and localhost MCP binding.
Secrets stay in Vault-backed environment/protected files rather than JSON.

At boot, local-disk `nfs-nas.service` calls a strict idempotent helper. It accepts
an already-mounted target only when source and filesystem match, otherwise fails
closed. Docker has `Requires=` and `After=` on that unit. Adoption installs boot
files but does not remount NFS or restart Docker.

Diagnostics retain two privilege layers:

```text
MCP client -> private tunnel -> 127.0.0.1:8765 on BenBeast
                                  |
                                  +-> HA/MQTT read-only adapters
                                  +-> bounded SSH as chatgpt-diag
                                        +-> constrained non-sudo runner
                                        +-> hlctl -> group-only Unix socket
                                                     -> root fixed-op probe
```

The installed wheel, configuration, audit state, gateway SSH key, mount helpers,
and systemd units reside on local disk. NAS loss therefore does not remove the
diagnostic plane. Backups include only rebuild-relevant local configuration and
remain a same-NAS convenience copy, not independent disaster recovery.
