# Exact rollback procedures

Ansible `backup: true` creates a timestamped sibling before replacing each adopted
file. Before each phase, record the generated backup filenames from Ansible output.
Rollback never touches application data, radio datasets, or watchdog state.

For a changed file, restore its recorded backup and validate before reload:

```sh
sudo install -o root -g root -m 0644 /path/to/file.TIMESTAMP~ /path/to/file
sudo systemd-analyze verify /etc/systemd/system/CHANGED.service
sudo systemctl daemon-reload
```

Phase-specific rollback:

1. Observer: first restore the previously reviewed version/URL/SHA pin and its
   matching schema-compatible JSON, then run check mode. A separately approved
   apply reinstalls that wheel in the same venv. If access itself must be removed,
   preserve evidence, disable `homelab-probe-agent.service`, restore prior SSH
   files, validate `sshd -t`, then explicitly approve the SSH reload. Do not remove
   the account until access logs and scratch files are reviewed.
2. Pi reporter/Code Tunnel: restore the exact `.bak`/Ansible backup for config,
   script, and unit; `daemon-reload`; only with explicit approval restart the one
   affected service. Never copy tunnel state from another host.
3. OTBR watchdog: restore script/service/timer backups, `daemon-reload`, and leave
   `/var/lib/otbr-watchdog/state` untouched. Never restart OTBR for rollback.
4. Gateway: disable only `homelab-observer-gateway.service`, restore prior local
   files if any, and retain the audit/key directory until reviewed. No HA change is
   required because the gateway only reads HA.
5. NFS/Docker boot files: restore `nfs-nas.service`, helper, and Docker drop-in,
   then `daemon-reload`. Do not restart Docker or remount NFS. Validate restored
   behaviour only in a separately approved reboot window.
6. Backup: disable the new timer; do not delete restic repositories/snapshots.
   Restore the old cron line only if it was explicitly retired and confirm no
   duplicate schedules.

If access is lost, use an existing independent console/tunnel path. If NFS is
unexpected, stop; do not force-mount over it. If OTBR degrades, preserve logs and
follow the existing watchdog/reboot cooldown rather than manual radio changes.
