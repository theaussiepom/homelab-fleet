# Fleet catalog projection

`homelab-site/catalog/site.json` is the one editable private site catalog.
Its `fleet_management` section carries the retained fleet policy and fixed source
records; the existing `fleet`/guest sections describe future placement intent.
These have different roles: retaining a legacy baseline does not admit future PVE
or host changes. There is no second editable inventory tree.

Generate a new private projection, then validate it before any Ansible invocation:

```sh
python scripts/fleet_catalog.py --catalog "$HOMELAB_SITE_CATALOG" --out "$HOMELAB_FLEET_INVENTORY"
python scripts/check-inventory --catalog "$HOMELAB_SITE_CATALOG" --inventory "$HOMELAB_FLEET_INVENTORY" --skip-secrets
```

The destination must be new and outside this checkout for production catalogs.
Files are private (0700 directory, 0600 files). Do not edit generated files:
validation binds their exact bytes and file set to the current catalog, rejecting
missing, extra, changed or symlinked files. Catalog membership, primary NFS pairs,
observer release pins and false mutation flags are still checked. A successful
projection is not deployment approval. Preserve the original private source and
historical acceptance receipts.

`audit-fleet`, `verify-fleet` and `enrol-pi` require both environment paths and
validate the projection before contacting hosts. Ansible has no default production
inventory. Direct playbook callers must perform the same validation and pass `-i`
explicitly. Existing maintenance/admission gates still apply.

The Zabbix role now receives its exact admitted host set, controller identity and
lazy-overlay exception identity from the private catalog. Empty/unknown contracts
fail before host access. Public tests use invented aliases and documentation
addresses; they do not assert current live acceptance.

For source-only checks, `make inventory-check` generates a disposable synthetic
projection; `pytest` uses temporary fixtures. No fleet hosts are contacted.

---

> Uncommitted split draft: production inventory is intentionally absent. A reviewed projection from the sole private site catalog is required before these fleet playbooks can execute. See SPLIT-DRAFT.md.

# homelab-fleet

Private, declarative fleet management for the existing Home Lab hosts. This
repository owns Ansible inventory, adoption and enrolment, NFS-before-Docker boot
ordering, Code Tunnel, Pi telemetry, configuration-only backups, the OTBR
watchdog, and the host-specific deployment policy for read-only diagnostics.

The observer application is an independent release dependency:

```text
homelab-observer v0.1.0 wheel
          |
          | exact URL + SHA-256
          v
homelab-fleet -> /opt/homelab-observer/venv
              -> /etc/homelab-observer/runtime.json
```

There is no observer Python source in this repository. Inventory generates the
versioned runtime configuration; the released application never parses Ansible.
The committed pin is in `${HOMELAB_FLEET_INVENTORY}/group_vars/all.yml`, and the update,
rollout, and rollback procedure is in `docs/observer-release.md`.

No playbook applies production changes automatically. Start locally with:

```sh
uv sync --all-groups
make test
uv run ansible-playbook playbooks/discover.yml
uv run ansible-playbook playbooks/adopt.yml --check --diff \
  -e homelab_observer_local_artifact=/absolute/path/to/reviewed.whl
```

The local artifact must match the committed SHA-256. Omit that override only after
the exact private release asset exists and is accessible to the managed hosts.
Review `AGENTS.md`, `docs/retrofit.md`, `docs/rollback.md`, and Vault handling in
`docs/security.md` before any live application. Current evidence is under
`reports/`; historical reports remain clearly labelled.
