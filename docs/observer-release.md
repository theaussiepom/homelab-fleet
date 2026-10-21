> Split layout: first generate and validate the private catalog projection described in README.md. Commands below require HOMELAB_FLEET_INVENTORY; historical receipts are not current acceptance.

# Pinning and updating homelab-observer

Fleet consumes one immutable observer wheel through three committed variables in
`${HOMELAB_FLEET_INVENTORY}/group_vars/all.yml`: `homelab_observer_version`,
`homelab_observer_release_url`, and `homelab_observer_sha256`. Schema support is an
independent explicit pin. Update all four together; never use a branch URL, latest
redirect, editable checkout, Git clone, or copied source.

## Update procedure

1. In `homelab-observer`, check a clean release commit, run `make test`, build the
   wheel, and calculate `shasum -a 256 dist/*.whl`.
2. Publish that exact wheel under tag `vVERSION` in the private observer repository.
3. Change fleet's version, exact release asset URL, and SHA-256. Change schema only
   after both repositories intentionally add compatibility.
4. Run `make test` in both repositories.
5. Before publishing or while testing the exact built bytes, exercise fleet check
   mode with an absolute controller-local path:

   ```sh
   uv run ansible-playbook playbooks/adopt.yml --check --diff \
     --limit 'Pironman:ZigbeePi:LoungeOTBR' \
     -e homelab_observer_local_artifact=/absolute/path/homelab_observer-VERSION-py3-none-any.whl
   ```

6. Verify the release URL independently, rerun check/diff without the local
   override, review every proposed change, and obtain explicit approval before an
   apply. Roll out one Pi at a time, then BenBeast with its existing sudo gate.

The role verifies a local override on the controller and `get_url` verifies a
release on the host. Live installation validates `runtime.json` with the installed
package before service activation. Secrets remain in encrypted `vault.yml`; the
JSON contains only endpoints and policy.

Because the observer repository is private, prefer downloading the exact release
asset on the controller with authenticated `gh release download`, checking its
SHA-256, and passing its absolute path as the local override. If managed hosts must
download directly, define `vault_observer_release_headers` only in encrypted Vault;
the download task suppresses output and still enforces the same SHA-256.

## Rollback

Revert to the previous known-good version/URL/SHA/schema tuple, retain both wheel
assets, run the same tests and check/diff, and apply only after approval. Do not
delete the newer artifact or logs until the incident is understood. A wheel
rollback never authorises a service restart, Docker action, mount change, or radio
change; those gates remain separate.
