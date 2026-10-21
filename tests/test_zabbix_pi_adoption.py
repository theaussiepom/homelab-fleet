"""Pi adoption and rendered Compose checks; no daemon, SSH or credentials."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from catalog_fixture import inventory_data
from test_zabbix_agent import ROLE, ROOT, read_yaml, render, run_validation, variables

HOSTS = ["PiOne", "PiTwo", "PiThree"]
DOCKER = shutil.which("docker")


def inventory_values(host: str) -> dict[str, Any]:
    inventory = inventory_data("zabbix.yml")
    group = inventory["all"]["children"]["zabbix_agents"]["children"]["zabbix_pi_agents"]
    result: dict[str, Any] = variables(host) | group["vars"] | group["hosts"][host]
    return result


def test_role_requires_explicit_private_identity_contract() -> None:
    defaults = read_yaml(ROLE / "defaults/main.yml")
    assert defaults["zabbix_agent_admitted_hosts"] == []
    assert defaults["zabbix_agent_controller_host"] == ""
    assert defaults["zabbix_agent_lazy_overlay_host"] == ""
    assert defaults["zabbix_agent_root_anchor_approved"] is False
    validation = (ROLE / "tasks/validate.yml").read_text()
    assert "inventory_hostname in zabbix_agent_admitted_hosts" in validation
    assert "inventory_hostname == zabbix_agent_lazy_overlay_host" in validation


def test_playbook_selects_only_pis_and_checks_synthetic_adoption_ids() -> None:
    play = read_yaml(ROOT / "playbooks/zabbix-agents.yml")[0]
    assert play["hosts"] == "zabbix_pi_agents"
    assert play["serial"] == 1 and play["any_errors_fatal"] is True
    fixture = json.loads((ROOT / "tests/fixtures/zabbix-pi-source.json").read_text())
    assert {
        host: inventory_values(host)["zabbix_agent_expected_container_id"] for host in HOSTS
    } == fixture["synthetic_container_ids"]
    assert all(not inventory_values(host)["zabbix_agent_root_anchor_approved"] for host in HOSTS)


def test_anchor_bootstrap_refuses_default_before_host_access(tmp_path: Path) -> None:
    play = read_yaml(ROOT / "playbooks/zabbix-pi-root-anchor.yml")[0]
    assert play["hosts"] == "zabbix_pi_agents"
    assert play["tasks"][0]["ansible.builtin.assert"]["that"][0] == (
        "zabbix_agent_root_anchor_approved | default(false) | bool"
    )
    result = run_validation(tmp_path, {}, tasks=play["tasks"][:1])
    assert result.returncode != 0
    assert "changed=0" in result.stdout
    copy = play["tasks"][-1]["ansible.builtin.copy"]
    assert copy == {
        "dest": "/.homelab-zabbix-rootfs.anchor",
        "content": "",
        "owner": "root",
        "group": "root",
        "mode": "0444",
        "force": False,
    }


@pytest.mark.parametrize("host", HOSTS)
def test_synthetic_agent_render_keeps_identity_and_transport(host: str) -> None:
    values = inventory_values(host)
    config = render("zabbix_agent2.conf.j2", values)
    assert "\nHostname=" + host + "\n" in config
    assert "\nServerActive=zabbix-server:10051\n" in config
    assert "\nServer=" not in config
    assert config.rstrip().endswith("DenyKey=*")
    assert values["zabbix_agent_transport_mode"] == "unencrypted"
    assert not values["zabbix_agent_root_anchor_approved"]


@pytest.mark.skipif(DOCKER is None, reason="Docker Compose CLI not installed")
@pytest.mark.parametrize("host", HOSTS)
def test_synthetic_inventory_renders_one_narrow_active_agent(tmp_path: Path, host: str) -> None:
    values = inventory_values(host) | {"zabbix_agent_compose_dir": str(tmp_path)}
    (tmp_path / "zabbix-agent.env").write_text(render("agent.env.j2", values))
    compose = tmp_path / "compose.yaml"
    compose.write_text(render("compose.yaml.j2", values))
    result = subprocess.run(
        [
            str(DOCKER),
            "compose",
            "--env-file",
            "/dev/null",
            "--project-name",
            "fixture",
            "-f",
            str(compose),
            "config",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    model = json.loads(result.stdout)
    name = "zabbix-agent-" + host.lower()
    assert list(model["services"]) == [name]
    service = model["services"][name]
    assert (
        service["image"] == values["zabbix_agent_image"] + "@" + values["zabbix_agent_image_digest"]
    )
    assert service["user"] == "1997:1995" and service["read_only"] is True
    assert service["platform"] == "linux/arm64" and service["pull_policy"] == "never"
    assert service["entrypoint"] == ["/usr/sbin/zabbix_agent2"]
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]
    assert not service.get("ports") and not service.get("privileged", False)
    assert not service.get("network_mode")
    assert list(service["networks"]) == ["underground"]
    network = model["networks"]["underground"]
    assert network["name"] == "underground" and network["external"] is True
    assert not network.get("ipam")  # Compose may normalize this to an empty object.
    assert len(service["volumes"]) == 2
    anchor = service["volumes"][-1]
    assert anchor["source"] == "/.homelab-zabbix-rootfs.anchor"
    assert anchor["target"] == "/var/lib/zabbix/fs/root"
    assert all(mount["read_only"] for mount in service["volumes"])
    assert all(
        not mount.get("bind", {}).get("create_host_path", False) for mount in service["volumes"]
    )
    assert service["environment"]["ZBX_TLSCONNECT"] == "unencrypted"
    assert not any("PSK" in key for key in service["environment"])
    config = render("zabbix_agent2.conf.j2", values)
    assert "\nHostname=" + host + "\n" in config
    assert "\nServerActive=zabbix-server:10051\n" in config and "\nServer=" not in config
    assert "AllowKey=vfs.fs.size[/var/lib/zabbix/fs/root,*]" in config
    assert config.rstrip().endswith("DenyKey=*")
