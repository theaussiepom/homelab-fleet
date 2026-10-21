"""Exercise a private helper fixture; never invoke real mount or systemd."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from catalog_fixture import inventory_data
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "nas:/export"
TARGET = "/mnt/nas/docker"
GOOD = f"{SOURCE} nfs4 {TARGET} rw,hard"


def run_helper(
    tmp_path: Path,
    row: str,
    rc: int = 0,
    *,
    check: bool = True,
    after: str = GOOD,
    mount_rc: int = 0,
) -> tuple[int, list[str]]:
    tmp_path.chmod(0o700)
    calls = tmp_path / "calls"
    marker = tmp_path / "mounted"
    fake = tmp_path / "command"
    fake.write_text("""#!/usr/bin/env python3
import json, os, pathlib, sys
command = sys.argv[1]
with open(os.environ['CALLS'], 'a') as f:
    f.write(command + '\\n')
if command == 'findmnt':
    assert '--mountpoint' in sys.argv and '--target' not in sys.argv
    if os.environ['ROW'] == 'stderr-error':
        print('inspection failed', file=sys.stderr)
        sys.exit(1)
    assert sys.argv[sys.argv.index('--output') + 1] == 'SOURCE,FSTYPE,TARGET,OPTIONS'
    assert '--kernel' in sys.argv and '--nocanonicalize' in sys.argv
    mounted = pathlib.Path(os.environ['MARKER']).exists()
    row = os.environ['AFTER'] if mounted else os.environ['ROW']
    if row:
        print(row)
    sys.exit(0 if mounted else int(os.environ['RC']))
if command == 'mount':
    pathlib.Path(os.environ['MARKER']).touch()
    sys.exit(int(os.environ['MOUNT_RC']))
assert command == 'mkdir'
""")
    fake.chmod(0o700)
    source = (ROOT / "roles/nfs_docker/files/homelab-nfs-ensure").read_text()
    for command in ("findmnt", "mkdir", "mount"):
        source = source.replace(f"/usr/bin/{command}", f"{fake} {command}")
    helper = tmp_path / "helper"
    helper.write_text(source)
    env = dict(
        os.environ,
        CALLS=str(calls),
        MARKER=str(marker),
        ROW=row,
        RC=str(rc),
        AFTER=after,
        MOUNT_RC=str(mount_rc),
    )
    result = subprocess.run(
        ["bash", str(helper), *(["--check-only"] if check else []), SOURCE, TARGET, "rw,hard"],
        env=env,
        capture_output=True,
    )
    return result.returncode, calls.read_text().splitlines()


@pytest.mark.parametrize("row", [GOOD, GOOD.replace("nfs4", "nfs")])
def test_correct_mount_is_never_mutated(tmp_path: Path, row: str) -> None:
    assert run_helper(tmp_path, row, check=False) == (0, ["findmnt"])


@pytest.mark.parametrize(
    "row,rc",
    [
        ("", 1),
        (GOOD.replace(SOURCE, SOURCE + "-wrong"), 0),
        (GOOD.replace(SOURCE, "prefix" + SOURCE), 0),
        (GOOD.replace("nfs4", "ext4"), 0),
        (GOOD.replace(TARGET, "/"), 0),
        (GOOD.replace("rw,", "ro,"), 0),
        (GOOD + " extra", 0),
        (GOOD + "\n" + GOOD, 0),
        ("malformed", 0),
        ("", 2),
        ("stderr-error", 1),
        ("", 0),
        (GOOD, 1),
        (GOOD.replace("rw,hard", "rw,ro"), 0),
    ],
)
def test_invalid_or_absent_check_never_mutates(tmp_path: Path, row: str, rc: int) -> None:
    result, calls = run_helper(tmp_path, row, rc)
    assert result != 0
    assert calls == ["findmnt"]


@pytest.mark.parametrize("row,rc", [(GOOD.replace(SOURCE, "wrong:/export"), 0), ("", 2)])
def test_unsafe_mount_capable_check_never_repairs(tmp_path: Path, row: str, rc: int) -> None:
    result, calls = run_helper(tmp_path, row, rc, check=False)
    assert result != 0
    assert calls == ["findmnt"]


@pytest.mark.parametrize(
    "after,mount_rc,success",
    [
        (GOOD, 0, True),
        ("", 0, False),
        (GOOD.replace(SOURCE, "wrong:/export"), 0, False),
        (GOOD, 32, False),
    ],
)
def test_absent_boot_mount_revalidated(
    tmp_path: Path, after: str, mount_rc: int, success: bool
) -> None:
    result, calls = run_helper(tmp_path, "", 1, check=False, after=after, mount_rc=mount_rc)
    assert (result == 0) is success
    assert calls[:3] == ["findmnt", "mkdir", "mount"]
    assert (calls[-1] == "findmnt") is (mount_rc == 0)


def test_both_export_units_and_adoption_contract() -> None:
    defaults = inventory_data("group_vars/docker_hosts.yml")
    host = inventory_data("host_vars/Controller.yml")
    template_root = ROOT / "roles/nfs_docker/templates"
    for hostvars in (host, {"nfs_boot_mounts": [host["nfs_boot_mounts"][0]]}):
        context = defaults | hostvars
        # Systemd templates contain no HTML.
        rendered = {
            name: Environment(autoescape=False)  # noqa: S701
            .from_string((template_root / name).read_text())
            .render(**context)
            for name in ("nfs-nas.service.j2", "docker-override.conf.j2")
        }
        docker = rendered["docker-override.conf.j2"]
        assert docker.count("ExecStartPre=") == len(context["nfs_boot_mounts"])
        assert "ExecStartPre=-" not in docker and "BindsTo=" not in docker
        assert ("nfs-dev.service" in docker) is (hostvars is host)
        for mount in context["nfs_boot_mounts"]:
            assert f"--check-only {mount['source']} {mount['target']}" in docker
        if hostvars is host:
            dev_mount = next(
                mount for mount in host["nfs_boot_mounts"] if mount["target"] == "/mnt/nas/dev"
            )
            assert (
                f"--check-only {dev_mount['source']} /mnt/nas/dev" in rendered["nfs-nas.service.j2"]
            )
            assert "Requires=nfs-dev.service" in rendered["nfs-nas.service.j2"]
            assert "After=network-online.target nfs-dev.service" in rendered["nfs-nas.service.j2"]
    tasks = (ROOT / "roles/nfs_docker/tasks/main.yml").read_text()
    assert "--mountpoint" in tasks and "--target" not in tasks
    assert "item.item.source in item.stdout" not in tasks
    assert "20-homelab-nfs-preflight.conf" in tasks
    assert "dest: /etc/systemd/system/docker.service.d/override.conf" not in tasks
    flags = inventory_data("group_vars/all.yml")
    assert not any(v for k, v in flags.items() if k.startswith("homelab_allow_"))
