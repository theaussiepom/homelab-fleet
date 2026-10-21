# New Pi onboarding

Add the host once under `managed_hosts`, `docker_hosts`, `raspberry_pis`,
`telemetry_hosts`, `code_tunnel_hosts`, `backup_hosts`, and `observer_hosts`.
Create host variables for its unique NFS mapping, capabilities, reporter base
topic/sensor/client ID, Code Tunnel name, service/container allowlists, and
staggered backup delay. Do not copy an existing Pi's reporter IDs or Code identity.
The current observer wheel pin must already be published and schema-compatible;
new hosts never clone either repository.

Validate and check first:

```sh
scripts/check-inventory --catalog "$HOMELAB_SITE_CATALOG" --inventory "$HOMELAB_FLEET_INVENTORY"
uv run ansible-playbook -i "$HOMELAB_FLEET_INVENTORY/hosts.yml" playbooks/bootstrap.yml --check --diff \
  -e target_host=GaragePi --limit GaragePi
uv run ansible-playbook -i "$HOMELAB_FLEET_INVENTORY/hosts.yml" playbooks/enrol-pi.yml --check --diff \
  -e target_host=GaragePi --limit GaragePi
```

After review and explicit approval:

```sh
HOMELAB_APPLY_APPROVED=YES scripts/enrol-pi GaragePi
```

The enrolment script deliberately fails closed unless Vault values exist for the
reporter, restic, observer SSH path, MCP, and Home Assistant. It runs one checked
restic backup, requires two non-retained MQTT publications and fresh distinct HA
state, exercises `hlctl` locally and through BenBeast's forced-command SSH path,
then writes `reports/GaragePi-admission.md`. It cannot print `HOST ADMITTED` before
those gates pass.

If the tunnel needs its one-time host-local login, run exactly:

```sh
sudo /usr/local/bin/code tunnel user login
```

Then rerun enrolment. A host remains unadmitted until the tunnel is enabled,
active, and not restart-looping; two MQTT publications are observed; HA has a
distinct device/unique IDs and fresh state; one restic backup/check succeeds;
observer access works; and mandatory units are healthy.

The reviewed lazy-overlay exception also requires
`zabbix_agent_admitted_lazy_overlay_swarm_node_id` in the private catalog. Populate
it with the separately verified Swarm node identity before materializing inventory.
The public example uses a synthetic identifier; it admits no existing host.
