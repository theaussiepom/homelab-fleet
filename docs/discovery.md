# Read-only discovery

Run:

```sh
uv run ansible-playbook playbooks/discover.yml
```

The play reads facts, NFS mounts, bounded systemd properties, Code CLI versions,
and Docker names/images/status. It writes `reports/current-state.json` and `.md`
on the controller. It does not use raw unit environments, container environments,
Home Assistant storage, reporter credentials, or other secret-bearing sources.

Targeted initial discovery additionally compared SHA-256 hashes and redacted
configuration. Both watchdog units/timers are identical; scripts differ only in
one comment, so the generic Pironman script was adopted. All reporter executable
hashes match. Read-only discovery corrected two historical assumptions: ZigbeePi
Code Tunnel is currently enabled/active, and LoungeOTBR already has the reporter
enabled/active. Live runtime details are preserved in the current-state and final
reports.

If a host is unavailable, record it rather than removing it from inventory or
inventing defaults. If a file differs from the discovered canonical hash, the
role fails closed and requires review.
