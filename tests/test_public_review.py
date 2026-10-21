"""Synthetic inputs for reviewed fleet failure paths; no managed host access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jinja2
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> Any:
    return yaml.safe_load((ROOT / name).read_text())


def environment() -> jinja2.Environment:
    env = jinja2.Environment(undefined=jinja2.ChainableUndefined)  # noqa: S701 - configuration, not HTML.
    env.filters["to_json"] = json.dumps
    env.globals.update(lookup=lambda *a, **kw: "storage.example.invalid", undef=lambda: None)
    return env


@pytest.mark.parametrize(
    "actual,accepted",
    [
        ("nas.example.invalid:/vol nfs4", True),
        ("nas.example.invalid:/vol nfs", True),
        ("nas.example.invalid:/vol2 nfs4", False),
        ("nas.example.invalid:/vol ext4", False),
        ("", False),
        ("nas.example.invalid:/vol nfs4\nother:/vol nfs4", False),
    ],
)
def test_nfs_verification_requires_exact_source(actual: str, accepted: bool) -> None:
    task = next(
        t for t in read("playbooks/verify.yml")[0]["tasks"] if "Verify declared NFS" in t["name"]
    )
    rejected = environment().compile_expression(task["failed_when"])(
        item={"source": "nas.example.invalid:/vol"}, verified_mount={"rc": 0, "stdout": actual}
    )
    assert not rejected if accepted else rejected


def test_discovery_handles_unreachable_host_and_empty_version() -> None:
    values = {
        "groups": {"managed_hosts": ["down", "up"]},
        "hostvars": {
            "down": {"ansible_facts": {}},
            "up": {
                "ansible_facts": {"hostname": "fixture"},
                "discovery_code_version": {"stdout_lines": []},
            },
        },
        "discovery_timestamp": {"stdout": "2000-01-01T00:00:00+11:00"},
    }
    env = environment()
    report = json.loads(
        env.from_string((ROOT / "playbooks/templates/current-state.json.j2").read_text()).render(
            **values
        )
    )
    assert report["hosts"]["down"]["reachable"] is False
    assert report["hosts"]["up"]["reachable"] is True
    rendered = env.from_string(
        (ROOT / "playbooks/templates/current-state.md.j2").read_text()
    ).render(**values)
    assert "Code Tunnel: `not found`" in rendered


@pytest.mark.parametrize("password", ['leading"quote', "back\\slash", 'both\\"', "unicode-é"])
def test_restic_environment_preserves_literal_values(password: str) -> None:
    env = environment()
    value = env.from_string(
        (ROOT / "roles/host_config_backup/templates/restic.env.j2").read_text()
    ).render(
        backup_mount_target="/backup", inventory_hostname="fixture", vault_restic_password=password
    )
    line = next(line for line in value.splitlines() if line.startswith("RESTIC_PASSWORD="))
    assert json.loads(line.split("=", 1)[1]) == password
    assert "\\u00e9" not in line


def test_admission_cannot_claim_telemetry_from_boolean_override() -> None:
    play = read("playbooks/admission-verify.yml")[0]
    checks = play["pre_tasks"]
    verifier = next(t for t in checks if "Verify fresh MQTT" in t["name"])
    assert verifier["ansible.builtin.command"]["argv"][-1] == "{{ inventory_hostname }}"
    assert verifier["delegate_to"] == "localhost" and verifier["become"] is False
    assert verifier["check_mode"] is False
    assert "failed_when" not in verifier and "ignore_errors" not in verifier
    assert (
        "telemetry_verification_passed" not in (ROOT / "playbooks/admission-verify.yml").read_text()
    )
