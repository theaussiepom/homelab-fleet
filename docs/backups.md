> Publication copy: deployment addresses and domains below are examples; restore private inputs before use.

# Encrypted configuration backups

The role mounts `192.0.2.1:/volume1/RaspberryPi` at `/backup` and uses
`/backup/restic/<inventory-hostname>/`. The root-only environment file is mode
0600 and receives its password only from Ansible Vault. Timers are staggered.

Included paths are rebuild-relevant systemd, Docker daemon, SSH daemon, fleet,
observer, selected local helper/service files, package inventory, root crontab,
network configuration when declared, and host-specific ser2net/Pironman/watchdog
configuration. Missing optional paths are skipped.

The script explicitly excludes `/docker`, `/mnt/nas`, `/var/lib/docker`, caches,
logs/runtime by omission, private keys, and `/var/lib/otbr-watchdog/state`.
Legacy rsync lines are preserved until a backup and `restic check` leave the local
success marker and `homelab_retire_legacy_backup=true` is explicitly supplied.
Retention values are daily 7, weekly 5, monthly 12, but `restic forget` remains
off until `homelab_allow_backup_forget=true` is separately approved because it
deletes snapshot references.

Approved initial execution:

```sh
ansible-playbook playbooks/backup.yml -e homelab_backup_execute=true --limit Pironman
```

Restore test into a temporary directory (never over live files):

```sh
restore_dir=$(mktemp -d /tmp/homelab-restic-restore.XXXXXX)
sudo --preserve-env=RESTIC_REPOSITORY,RESTIC_PASSWORD restic restore latest \
  --target "$restore_dir"
sudo diff -ruN /etc/homelab "$restore_dir/etc/homelab"
```

Remove the temporary directory only after review. This same-NAS copy is not an
independent disaster-recovery backup; Synology snapshots and off-NAS copies are
external responsibilities.
