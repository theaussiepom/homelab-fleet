# Operations

Common read-only commands:

```sh
scripts/audit-fleet
scripts/verify-fleet
scripts/collect-incident Pironman otbr --since-minutes 60
scripts/collect-incident ZigbeePi zigbee --since-minutes 30
```

Use focused MCP tools first. `collect_incident` correlates failed operations, NFS
and Docker state, bounded logs, service/restart state, OTBR REST/USB/watchdog,
reporter evidence, and HA observations. It does not concatenate unlimited logs.

OTBR healthy-path verification is limited to container running/health/restart
policy, REST `/node`, radio role as exposed by REST/live discovery, ZBT-2 USB,
timer state, and recent successful watchdog invocations. Never induce a hard RCP
failure. Do not invoke the watchdog manually while unhealthy.

NFS boot validation is a maintenance procedure: capture pre-state, approve one
host reboot, watch `nfs-nas.service`, verify exact mount sources, then verify Docker
and every host capability. Stop rollout on the first mismatch. Never manually
mount/unmount the production path during routine adoption.

Telemetry reports are written to `reports/telemetry-verification.{json,md}`. A
blocked report is evidence only of missing credentials—not reporter or HA failure.
