# Repository split plan

Recorded before destructive restructuring on 17 July 2026 (Australia/Sydney).

## Starting evidence

- Repository: `/Users/bennis/code/homelab-fleet`
- Branch and commit: `main` at `69d2ae8` (`Initial commit`)
- Remote: `origin` at `https://github.com/theaussiepom/homelab-fleet.git`
- The combined implementation is present as uncommitted work, so tagging the
  original `HEAD` would not preserve it.
- `/Users/bennis/code/homelab-observer` does not exist.
- No remote push, force-push, live-host apply, service action, mount action, or
  production mutation is part of this split.

## Safe history-preservation method

1. Commit the complete combined implementation and this plan as a baseline
   snapshot in `homelab-fleet`.
2. Create the annotated tag `monorepo-split-base` on that snapshot.
3. Use `git subtree split --prefix=observer` to create a temporary extracted
   history containing the observer directory at repository root.
4. Clone that extracted commit into `/Users/bennis/code/homelab-observer` and
   add its independent packaging, documentation, configuration schema, tests,
   lockfile, and release policy in a new commit.
5. Refactor `homelab-fleet` in a later commit: remove observer Python source and
   tests, retain inventory/deployment policy, and turn observer roles into thin
   pinned-wheel deployment roles.
6. Keep the baseline tag and all evidence reports. Mark the combined final report
   as historical and predating the split.

`git subtree split` is used only as a one-time history extractor. The final
repositories will have no submodule, subtree link, symlink, editable install, or
checkout-to-checkout source dependency.

## Ownership after the split

`homelab-observer` owns the generic typed Python package, console entrypoints,
runtime schema and validation, probe, constrained shell runner, gateway/MCP,
redaction, incident correlation, HA/MQTT adapters, telemetry verification
library, package tests, application security docs, changelog, and releases.

`homelab-fleet` retains Ansible inventory/playbooks, host facts, identity,
NFS/Docker ordering, Code Tunnel, reporter deployment, telemetry orchestration,
restic, watchdog, diagnostic account/SSH policy, generated observer runtime
configuration, pinned artifact installation, fleet tests, rollout, and rollback.

## Dependency and release contract

Dependency direction is one-way: observer builds a semantically versioned wheel;
fleet pins version, artifact URL, and SHA-256, downloads or copies that immutable
artifact, installs it into `/opt/homelab-observer/venv`, and renders schema-versioned
configuration under `/etc/homelab-observer`. Observer never reads Ansible inventory.

The initial split verifies a local wheel artifact. The committed fleet default
documents the corresponding immutable release URL, but production deployment
waits until that release exists and receives separate approval.

## Destructive-operation boundary and rollback

No source is removed from `homelab-fleet` until the baseline commit/tag and the
independent observer checkout are verified. If restructuring fails, stop and
return to the still-existing `monorepo-split-base` commit in a separate worktree;
do not reset, force-push, or delete either checkout. The original remote and tag
remain untouched unless a later explicit push is approved.
