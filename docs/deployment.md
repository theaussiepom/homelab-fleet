# Standalone and integrated private deployment

Select exact reviewed releases of homelab and homelab-fleet. Create one private site repository with actual catalog, release pins and protected-store references following the common setup guide. For a Pi-only deployment use the fleet synthetic example as the data shape; for an integrated estate use the same private catalog as the PVE guests. Set `HOMELAB_IMPLEMENTATION_ROOT` to the pinned common code; do not copy its Python implementation into this repository or the private site.

Preserve trusted per-host keys/fingerprints, existing accounts/IDs and old recovery access. Derive automation sources and controller policy from admitted deploy/external-workstation bindings; do not copy an old Beast-only source constraint and expect it to work from another address. Initial trust is established independently, never accepted merely from ssh-keyscan.

Install the exact hashed Python closure in a local environment and run syntax checks from this repository:

```bash
ansible-playbook -i localhost, --syntax-check playbooks/discover.yml
ansible-playbook -i localhost, --syntax-check playbooks/stage-network.yml
```

Before a later host operation, render the same private catalog through common tooling and bind reviewed per-host immutable profile files/hashes/native parser receipts. Pass only that selected private inventory. Mutation flags default false; role qualification, check/diff, exact target changes and existing explicit live-operation authority still apply. Staging requires a source hash, disabled autoconnect and no unexpected existing destination; the role never activates/reloads a profile.

Public CI is hosted and has no private runner/credentials. Private CI invokes these public playbooks/common commands from reviewed pins through its admitted private runner and global execution/approval policy. Real secrets, reports, inventory, fabrics and native backup artifacts stay private.
