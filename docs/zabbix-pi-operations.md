> Split layout: first generate and validate the private catalog projection described in README.md. Commands below require HOMELAB_FLEET_INVENTORY; historical receipts are not current acceptance.

# Existing Pi Zabbix agents

Source reconciliation recorded 3 October 2026 (Australia/Brisbane). This captures
the installed three-Pi setup; copying these source files requires no service
change. The initial central baseline was accepted at 11:57 AEST that day.
Pironman, ZigbeePi and LoungeOTBR each reported CPU idle, available memory and
root-filesystem used percentage. That evidence does not establish every allowed
metric or independently verify the active heartbeat protocol.

Fresh read-only inspection at 15:58 AEST on 3 October confirmed the same three
container IDs, running with zero restarts. Managed Compose, config, nonsecret
environment-file and anchor hashes matched their installed baseline. The local
test fixture preserves those metadata observations; rendering with Ansible's
whitespace defaults and each observed config-fingerprint label matches all nine
managed-file hashes. This is recorded evidence, not a substitute for fresh
discovery before a later apply.

## Ownership and current configuration

The Pi-only overlay is `${HOMELAB_FLEET_INVENTORY}/zabbix.yml`; load it alongside the
normal `${HOMELAB_FLEET_INVENTORY}/hosts.yml`. `playbooks/zabbix-agents.yml` selects
only `zabbix_pi_agents`. The deployed role is preserved byte-for-byte, including
unused BenBeast branches; this overlay does not select or approve those branches.
BenBeast monitoring Compose, agent version and central Zabbix configuration are
outside this adoption.

Each Pi owns `/etc/homelab/zabbix-agent/compose.yaml`, `zabbix_agent2.conf` and
`zabbix-agent.env`, managed by this role. The local Compose project is
`zabbix-agent`, with one service/container `zabbix-agent-<lowercase Pi name>`.
These files stay on local disk. There is no new central Compose project.

The installed image is `zabbix/zabbix-agent2:alpine-7.0.31`, ARM64, pinned to
`sha256:90547dfac57596d500f85e022d00d7ea47ed9b46fd80fd5a027d039dbabb6fea`.
Pironman and ZigbeePi report config ID
`sha256:525da77bced818c01390082df267ed631b6d7de0e5155c46a44bbbe5c26fefd2`;
LoungeOTBR's reviewed image store reports the manifest digest as its image ID.
The inventory retains that exact per-host difference and never falls back to
accepting either ID indiscriminately.

Runtime UID:GID is `1997:1995`; image USER is `1997`. The agent runs directly
with a read-only root, bounded `/tmp` tmpfs, dropped capabilities and no new
privileges. It uses only the existing attachable `underground` overlay, ID
`nfg7i5cyjo1mbobzoexvxpq5a`. There are no published ports, host networking,
Docker socket, privileged access or root-directory bind mount.

Each exact Pi hostname sends unencrypted active checks to
`zabbix-server:10051`, as separately approved. Passive checks remain disabled.
The root-capacity anchor is the existing empty root-owned regular file
`/.homelab-zabbix-rootfs.anchor`, mode `0444`, on the ext4 `/` filesystem.
It is mounted read-only at `/var/lib/zabbix/fs/root`; the allowlist grants
filesystem statistics there and ends with `DenyKey=*`.

## Safe adoption and future changes

Every write/start approval remains false, including overlay attachment and the
separate anchor bootstrap. The three accepted container IDs are recorded as a
fail-closed adoption baseline, not as permanent proof of current live state.
Before any approved apply, refresh container/image IDs, project/service labels,
Swarm/overlay identity, managed-file hashes/metadata, and unrelated-service
baseline. A missing or replaced agent must fail the existing-ID checks; do not
clear an ID to bypass adoption review.

Local syntax checking does not contact the hosts:

```sh
uv run ansible-playbook -i ${HOMELAB_FLEET_INVENTORY}/hosts.yml \
  -i ${HOMELAB_FLEET_INVENTORY}/zabbix.yml --syntax-check playbooks/zabbix-agents.yml
uv run ansible-playbook -i ${HOMELAB_FLEET_INVENTORY}/hosts.yml \
  -i ${HOMELAB_FLEET_INVENTORY}/zabbix.yml --syntax-check playbooks/zabbix-pi-root-anchor.yml
uv run pytest -q tests/test_zabbix_agent.py tests/test_zabbix_pi_adoption.py
```

Before live application follow `AGENTS.md`: fresh discovery, relevant local
tests/lint, a reviewed `--check --diff` preparation run, exact proposed changes,
then explicit approval. Default-disabled checks alone do not exercise enabled
preparation. Keep deploy disabled for preparation; activation explicitly refuses
check mode. Use a separate reviewed invocation limited to one Pi with all required
gates, and preserve unrelated services. The role backs up replaced managed files
and uses targeted `compose up --no-deps --pull never --no-build` only.

The anchor bootstrap is separate and normally unnecessary after adoption. It
requires explicit `zabbix_agent_root_anchor_approved=true`, verifies root/ext4 and
existing-file metadata, and creates only an absent empty file. It never replaces
an existing mismatched path. Do not replay the historical first-attachment or
installation approvals.

For an image change, review official version/compatibility and ARM64 digest,
image ID and USER first; update the image, digest, validation allowlist, per-host
expected image identities and tests together. Acquire/verify the exact local
image only under separate approval: normal activation never pulls/builds.
Refresh each existing-container image baseline, inspect rendered changes, then
roll out and verify one Pi at a time. After an approved recreation, record its
new accepted ID before further runs. Keep the previous image and timestamped
configuration backups for a separately approved targeted rollback; never use
`compose down` or restart unrelated services.

Raw Compose-template bytes contribute to the config fingerprint. Even cosmetic
template edits can cause a later recreation. Preserve those bytes for this source
reconciliation; the test fixture records their hashes.

## Deferred PSKs and central changes

No PSK is created, copied or enabled by this reconciliation. PSK migration needs
separate secure provisioning, reviewed metadata/ownership and matching central
encryption settings, followed by an approved per-Pi cutover. The old operator
helper is intentionally excluded; its hardcoded image-ID check needs review for
LoungeOTBR before future use. Never put keys in inventory, reports or chat.

No central host/item creation manifest is included. Existing hosts/items must be
adopted from fresh API identities before any future central write; the earlier
new-host enrollment plan is historical and must not be replayed.
