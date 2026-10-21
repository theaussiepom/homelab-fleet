"""Local-only contract/render tests; no Docker, SSH, downloads or PSK bytes."""

from __future__ import annotations

from catalog_fixture import inventory_data

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import jinja2
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "roles" / "zabbix_agent"
ANSIBLE = Path(
    shutil.which("ansible-playbook") or Path(sys.executable).with_name("ansible-playbook")
)
BEAST_IMAGE_ID = "sha256:faae8fdfb48382b7ab0c93d1d07ac45465f2c13bf0b691ff08b4717e16eedc5b"
PI_DIGEST = "sha256:90547dfac57596d500f85e022d00d7ea47ed9b46fd80fd5a027d039dbabb6fea"
PI_IMAGE_ID = "sha256:525da77bced818c01390082df267ed631b6d7de0e5155c46a44bbbe5c26fefd2"
INTERIM_DIGEST = "sha256:e8b6bba220dd814eedb606c6a644ec38e17f20712bf1e5663e150ef3f00d87ed"


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def variables(host: str = "PiOne") -> dict[str, Any]:
    result: dict[str, Any] = read_yaml(ROLE / "defaults" / "main.yml")
    beast = host == "Controller"
    image_id = BEAST_IMAGE_ID if beast else PI_DIGEST if host == "PiThree" else PI_IMAGE_ID
    result.update(
        zabbix_agent_admitted_hosts=["Controller", "PiOne", "PiTwo", "PiThree"],
        zabbix_agent_controller_host="Controller",
        zabbix_agent_lazy_overlay_host="PiThree",
        zabbix_agent_admitted_overlay_network_id="x" * 25,
        inventory_hostname=host,
        zabbix_agent_enabled=True,
        zabbix_agent_existing_project=beast,
        zabbix_agent_canonical_integrated=beast,
        zabbix_agent_project_name="monitoring" if beast else "zabbix-agent",
        zabbix_agent_service_name="zabbix-agent" if beast else "zabbix-agent-" + host.lower(),
        zabbix_agent_container_name="zabbix-agent" if beast else "zabbix-agent-" + host.lower(),
        zabbix_agent_overlay_network="underground",
        zabbix_agent_overlay_network_id="xxxxxxxxxxxxxxxxxxxxxxxxx",
        zabbix_agent_swarm_node_id="a" * 25,
        zabbix_agent_compose_dir="/etc/homelab/zabbix-agent",
        zabbix_agent_image=BEAST_IMAGE_ID if beast else "zabbix/zabbix-agent2:alpine-7.0.31",
        zabbix_agent_image_digest="" if beast else PI_DIGEST,
        zabbix_agent_expected_image_id=image_id,
        zabbix_agent_expected_container_image_id=image_id,
        zabbix_agent_expected_container_id="b" * 64 if beast else "",
        zabbix_agent_canonical_sha256="c" * 64 if beast else "",
        zabbix_agent_runtime_uid=0 if beast else 1997,
        zabbix_agent_runtime_gid=0 if beast else 1995,
        zabbix_agent_verified_image_user="1997",
        zabbix_agent_image_user_verified=True,
        zabbix_agent_architecture="amd64" if beast else "arm64",
        zabbix_agent_hostname="zabbix-server" if beast else host,
        zabbix_agent_server_active="zabbix-server:10051",
        zabbix_agent_passive_server="zabbix-server" if beast else "",
        zabbix_agent_transport_mode="psk" if beast else "unencrypted",
        zabbix_agent_passive_tls_accept="unencrypted",
        zabbix_agent_secret_boundary_verified=beast,
        zabbix_agent_psk_identity="fixture-metadata-only" if beast else "",
        zabbix_agent_psk_file="/etc/protected-fixture-location/agent.psk" if beast else "",
        zabbix_agent_config_fingerprint="d" * 64,
    )
    return result


def render(name: str, values: dict[str, Any]) -> str:
    environment = jinja2.Environment(  # noqa: S701 - render YAML/agent config, never HTML.
        loader=jinja2.FileSystemLoader(ROLE / "templates"),
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
    )
    environment.filters["to_json"] = json.dumps
    return environment.get_template(name).render(**values)


def run_validation(
    tmp_path: Path,
    values: dict[str, Any],
    *,
    tasks: list[dict[str, Any]] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run only assertions/disabled role paths against a named localhost fixture."""
    host = values.get("inventory_hostname", "PiOne")
    (tmp_path / "inventory.yml").write_text(
        yaml.safe_dump({"all": {"hosts": {host: {"ansible_connection": "local"}}}})
    )
    (tmp_path / "vars.json").write_text(json.dumps(values))
    play = {"hosts": "all", "gather_facts": False}
    play.update({"roles": ["zabbix_agent"]} if tasks is None else {"tasks": tasks})
    (tmp_path / "play.yml").write_text(yaml.safe_dump([play]))
    environment = os.environ.copy()
    environment.update(
        ANSIBLE_CONFIG=str(tmp_path / "ansible.cfg"),
        ANSIBLE_ROLES_PATH=str(ROOT / "roles"),
        ANSIBLE_LOCAL_TEMP=str(tmp_path / "ansible-tmp"),
        ANSIBLE_NOCOLOR="1",
    )
    (tmp_path / "ansible.cfg").write_text("[defaults]\nretry_files_enabled=False\n")
    return subprocess.run(
        [
            str(ANSIBLE),
            "-i",
            str(tmp_path / "inventory.yml"),
            str(tmp_path / "play.yml"),
            "--check",
            "-e",
            "@" + str(tmp_path / "vars.json"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
        check=False,
    )


def test_defaults_cannot_write_start_or_restart(tmp_path: Path) -> None:
    defaults = read_yaml(ROLE / "defaults" / "main.yml")
    for name in [
        "enabled",
        "install_enabled",
        "deploy_enabled",
        "canonical_integrated",
        "version_change_approved",
        "maintenance_window_approved",
        "runtime_baseline_confirmed",
        "transport_ready",
        "version_compatibility_reviewed",
        "central_identity_confirmed",
        "overlay_attachment_approved",
        "overlay_absence_manager_verified",
    ]:
        assert defaults["zabbix_agent_" + name] is False
    assert defaults["homelab_allow_service_restart"] is False
    assert defaults["zabbix_agent_transport_mode"] == "psk"
    result = run_validation(tmp_path, {})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "changed=0" in result.stdout
    assert "Inspect only agent container identity" not in result.stdout


def test_pi_inventory_candidate_preserves_inactive_gates_and_adoption_baseline() -> None:
    defaults = read_yaml(ROLE / "defaults" / "main.yml")
    inventory = inventory_data('zabbix.yml')["all"]
    agents = inventory["children"]["zabbix_agents"]
    pis = agents["children"]["zabbix_pi_agents"]
    assert set(pis["hosts"]) == {"PiOne", "PiTwo", "PiThree"}
    assert "hosts" not in agents
    for host, host_vars in pis["hosts"].items():
        merged = (
            defaults | inventory.get("vars", {}) | agents.get("vars", {}) | pis["vars"] | host_vars
        )
        assert merged["zabbix_agent_image"] == "zabbix/zabbix-agent2:alpine-7.0.31"
        assert merged["zabbix_agent_image_digest"] == PI_DIGEST
        assert merged["zabbix_agent_expected_image_id"] == (
            PI_DIGEST if host == "PiThree" else PI_IMAGE_ID
        )
        assert merged["zabbix_agent_transport_mode"] == "unencrypted"
        assert merged["zabbix_agent_psk_identity"] == ""
        assert merged["zabbix_agent_psk_file"] == ""
        for gate in (
            "enabled",
            "install_enabled",
            "deploy_enabled",
            "version_change_approved",
            "maintenance_window_approved",
            "runtime_baseline_confirmed",
            "transport_ready",
            "version_compatibility_reviewed",
            "secret_boundary_verified",
            "central_identity_confirmed",
            "overlay_attachment_approved",
            "overlay_absence_manager_verified",
            "root_anchor_approved",
        ):
            assert merged["zabbix_agent_" + gate] is False
        assert merged["homelab_allow_service_restart"] is False
        assert len(merged["zabbix_agent_expected_container_id"]) == 64
        assert merged["zabbix_agent_expected_container_id"] != ""


def test_deploy_cannot_bypass_install_gate(tmp_path: Path) -> None:
    result = run_validation(tmp_path, {"zabbix_agent_deploy_enabled": True})
    assert result.returncode != 0
    assert "Inspect only agent container identity" not in result.stdout


@pytest.mark.parametrize("host", ["Controller", "PiOne", "PiTwo", "PiThree"])
def test_valid_metadata_only_validation_does_not_inspect_hosts(tmp_path: Path, host: str) -> None:
    result = run_validation(tmp_path, variables(host))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "changed=0" in result.stdout
    assert "Inspect only agent container identity" not in result.stdout


@pytest.mark.parametrize(
    "override",
    [
        {"zabbix_agent_image_digest": "latest"},
        {"zabbix_agent_image_digest": "sha256:" + "f" * 64},
        {"zabbix_agent_expected_image_id": "sha256:" + "a" * 64},
        {
            "zabbix_agent_expected_image_id": "sha256:" + "f" * 64,
            "zabbix_agent_expected_container_image_id": "sha256:" + "f" * 64,
        },
        {"zabbix_agent_image": "zabbix/zabbix-agent2:alpine-7.4.15"},
        {
            "zabbix_agent_image": "zabbix/zabbix-agent2:alpine-7.2.12",
            "zabbix_agent_image_digest": INTERIM_DIGEST,
        },
        {"zabbix_agent_image_user_verified": False},
        {"zabbix_agent_verified_image_user": "1997:1995"},
        {"zabbix_agent_runtime_uid": 0},
        {"zabbix_agent_hostname": "zabbix-server"},
        {"zabbix_agent_service_name": "zabbix-agent"},
        {"zabbix_agent_overlay_network": "new-network"},
        {"zabbix_agent_overlay_network_id": ""},
        {"zabbix_agent_server_active": "10.254.253.5:10051"},
        {"zabbix_agent_server_active": "10.254.253.5:10051;touch /tmp/no"},
        {"zabbix_agent_transport_mode": "cert"},
        {"zabbix_agent_passive_server": "127.0.0.1"},
        {"zabbix_agent_psk_identity": "unapproved-leftover"},
        {"zabbix_agent_psk_file": "/nonexistent/agent.psk"},
        {
            "zabbix_agent_filesystem_anchors": [
                {
                    "alias": "nfs_docker",
                    "source": "/mnt/nas",
                    "expected_mount": "/",
                    "expected_fstype": "ext4",
                }
            ]
        },
    ],
)
def test_invalid_runtime_and_anchor_inputs_fail_before_host_access(
    tmp_path: Path,
    override: dict[str, Any],
) -> None:
    result = run_validation(tmp_path, variables() | override)
    assert result.returncode != 0
    assert "Inspect only agent container identity" not in result.stdout


@pytest.mark.parametrize("host", ["PiOne", "PiThree"])
def test_observed_image_id_must_match_reviewed_host_convention_without_fallback(host: str) -> None:
    task = next(
        task
        for task in read_yaml(ROLE / "tasks" / "inspect.yml")
        if task["name"] == "Verify the installed image matches its approved discovery record"
    )
    environment = jinja2.Environment()  # noqa: S701 - evaluate an identity predicate, not HTML.
    matches = environment.compile_expression(task["ansible.builtin.assert"]["that"][0])
    values = variables(host)
    for observed in (PI_IMAGE_ID, PI_DIGEST, "sha256:" + "f" * 64):
        values["zabbix_agent_image_observed"] = {"stdout": observed + "|arm64|1997"}
        assert matches(**values) is (observed == values["zabbix_agent_expected_image_id"])


@pytest.mark.parametrize("host", ["PiOne", "PiTwo", "PiThree"])
def test_pi_render_is_unprivileged_active_only_and_has_no_host_interfaces(host: str) -> None:
    values = variables(host)
    model = yaml.safe_load(render("compose.yaml.j2", values))
    expected_name = "zabbix-agent-" + host.lower()
    assert list(model["services"]) == [expected_name]
    data = model["services"][expected_name]
    assert data["container_name"] == expected_name
    assert data["networks"] == ["underground"]
    assert model["networks"] == {"underground": {"external": True, "name": "underground"}}
    assert data["image"] == "zabbix/zabbix-agent2:alpine-7.0.31@" + PI_DIGEST
    assert data["user"] == "1997:1995"
    assert data["platform"] == "linux/arm64"
    assert data["read_only"] is True
    assert data["entrypoint"] == ["/usr/sbin/zabbix_agent2"]
    assert data["cap_drop"] == ["ALL"]
    assert data["security_opt"] == ["no-new-privileges:true"]
    assert not (
        {"ports", "network_mode", "pid", "devices", "privileged", "group_add"} & data.keys()
    )
    assert all(
        mount["read_only"] and not mount["bind"]["create_host_path"] for mount in data["volumes"]
    )
    assert all(
        "docker.sock" not in mount["source"] and mount["source"] != "/" for mount in data["volumes"]
    )
    config = render("zabbix_agent2.conf.j2", values)
    assert "\nHostname=" + host + "\n" in config
    assert "\nServerActive=zabbix-server:10051\n" in config
    assert "\nServer=" not in config and "StatusPort=" not in config
    assert "TLSConnect=unencrypted" in config and "TLSAccept=unencrypted" in config
    assert "ListenIP=127.0.0.1" in config
    assert "TLSPSK" not in config and "TLSPSK" not in render("agent.env.j2", values)
    assert len(data["volumes"]) == 1  # Only the explicit config, no PSK or broad host mount.
    assert "system.run" not in config and "Include=" not in config
    assert "UserParameter=" not in config and config.rstrip().endswith("DenyKey=*")
    assert "vfs.fs.size" not in config  # Unverified anchors produce no filesystem grant.


def test_beast_requires_explicit_canonical_integration_before_host_access(tmp_path: Path) -> None:
    result = run_validation(
        tmp_path, variables("Controller") | {"zabbix_agent_canonical_integrated": False}
    )
    assert result.returncode != 0
    assert "Inspect only agent container identity" not in result.stdout
    defaults = read_yaml(ROLE / "defaults" / "main.yml")
    assert defaults["zabbix_agent_canonical_integrated"] is False


def test_anchors_render_only_explicit_readonly_files_and_matching_keys() -> None:
    values = variables() | {
        "zabbix_agent_filesystem_anchors": [
            {
                "alias": "root",
                "source": "/var/lib/homelab/anchors/rootfs-capacity",
                "expected_mount": "/",
                "expected_fstype": "ext4",
            },
        ]
    }
    data = yaml.safe_load(render("compose.yaml.j2", values))["services"][
        values["zabbix_agent_service_name"]
    ]
    anchor = data["volumes"][-1]
    assert anchor["source"] == "/var/lib/homelab/anchors/rootfs-capacity"
    assert anchor["target"] == "/var/lib/zabbix/fs/root"
    assert anchor["read_only"] is True and anchor["bind"]["create_host_path"] is False
    assert "AllowKey=vfs.fs.size[/var/lib/zabbix/fs/root,*]" in render(
        "zabbix_agent2.conf.j2", values
    )


def test_psk_tasks_never_read_write_or_checksum_secret_bytes() -> None:
    tasks = read_yaml(ROLE / "tasks" / "inspect.yml")
    task = next(task for task in tasks if task["name"] == "Inspect external PSK file metadata only")
    assert task["no_log"] is True
    assert task["ansible.builtin.stat"]["get_checksum"] is False
    assert task["ansible.builtin.stat"]["get_mime"] is False
    assert task["ansible.builtin.stat"]["follow"] is False
    sources = "\n".join(path.read_text() for path in (ROLE / "tasks").glob("*.yml"))
    assert "ansible.builtin.slurp" not in sources
    assert "ansible.builtin.shell" not in sources
    assert "community.docker" not in sources
    assert "lookup('file'" not in sources


def test_unencrypted_pi_skips_all_psk_inspection_without_a_secret_file(tmp_path: Path) -> None:
    tasks = [task for task in read_yaml(ROLE / "tasks" / "inspect.yml") if "PSK" in task["name"]]
    assert len(tasks) == 3
    result = run_validation(tmp_path, variables(), tasks=tasks)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "skipped=3" in result.stdout and "changed=0" in result.stdout


def test_beast_cannot_select_pi_unencrypted_mode(tmp_path: Path) -> None:
    result = run_validation(
        tmp_path,
        variables("Controller")
        | {
            "zabbix_agent_transport_mode": "unencrypted",
            "zabbix_agent_psk_identity": "",
            "zabbix_agent_psk_file": "",
        },
    )
    assert result.returncode != 0
    assert "Inspect only agent container identity" not in result.stdout


def test_pi_psk_option_still_requires_verified_secret_metadata(tmp_path: Path) -> None:
    values = variables() | {
        "zabbix_agent_transport_mode": "psk",
        "zabbix_agent_passive_tls_accept": "psk",
        "zabbix_agent_psk_identity": "fixture-metadata-only",
        "zabbix_agent_psk_file": "/etc/protected-fixture-location/agent.psk",
    }
    result = run_validation(tmp_path, values)
    assert result.returncode != 0  # Secret boundary remains unverified.
    values["zabbix_agent_secret_boundary_verified"] = True
    result = run_validation(tmp_path, values)
    assert result.returncode == 0, result.stdout + result.stderr
    config = render("zabbix_agent2.conf.j2", values)
    assert "TLSConnect=psk" in config and "TLSAccept=psk" in config
    assert "TLSPSKIdentity=fixture-metadata-only" in config
    data = yaml.safe_load(render("compose.yaml.j2", values))["services"][
        values["zabbix_agent_service_name"]
    ]
    assert data["volumes"][1]["source"] == values["zabbix_agent_psk_file"]


@pytest.mark.parametrize("host", ["PiOne", "PiThree"])
def test_lazy_overlay_evidence_is_lounge_only(tmp_path: Path, host: str) -> None:
    values = variables(host) | {
        "zabbix_agent_overlay_absence_manager_verified": True,
        "zabbix_agent_overlay_attachment_approved": True,
        "zabbix_agent_swarm_node_id": "sogaa85jhenw6hdpsp0590tbh",
    }
    result = run_validation(tmp_path, values)
    assert (result.returncode == 0) is (host == "PiThree"), result.stdout + result.stderr


@pytest.mark.parametrize(
    ("approved", "rc", "stdout", "stderr", "accepted"),
    [
        (False, 0, "underground|xxxxxxxxxxxxxxxxxxxxxxxxx|overlay|swarm|true", "", True),
        (True, 1, "", "Error response from daemon: network underground not found", True),
        (False, 1, "", "Error response from daemon: network underground not found", False),
        (True, 1, "", "permission denied", False),
        (True, 1, "", "Cannot connect to the Docker daemon", False),
        (True, 2, "", "Error response from daemon: network underground not found", False),
        (True, 1, "unexpected", "Error response from daemon: network underground not found", False),
        (True, 0, "underground|different|overlay|swarm|true", "", False),
        (True, 0, "underground|xxxxxxxxxxxxxxxxxxxxxxxxx|bridge|local|true", "", False),
    ],
)
def test_overlay_preflight_accepts_only_exact_metadata_or_reviewed_absence(
    approved: bool,
    rc: int,
    stdout: str,
    stderr: str,
    accepted: bool,
) -> None:
    tasks = read_yaml(ROLE / "tasks" / "inspect.yml")
    probe = next(task for task in tasks if task["name"].startswith("Inspect the existing external"))
    gate = next(
        task for task in tasks if task["name"].startswith("Require the reviewed attachable")
    )
    values = variables("PiThree") | {
        "zabbix_agent_overlay_absence_manager_verified": approved,
        "zabbix_agent_overlay_observed": {"rc": rc, "stdout": stdout, "stderr": stderr},
    }
    environment = jinja2.Environment()  # noqa: S701 - evaluate fixed predicates, not HTML.
    failed = environment.compile_expression(probe["failed_when"])(**values)
    assertion = environment.compile_expression(gate["ansible.builtin.assert"]["that"][0])(**values)
    assert (not failed and assertion) is accepted


@pytest.mark.parametrize(
    ("metadata", "attachment", "accepted"),
    [
        (
            "underground|xxxxxxxxxxxxxxxxxxxxxxxxx|overlay|swarm|true",
            "1|xxxxxxxxxxxxxxxxxxxxxxxxx",
            True,
        ),
        ("underground|different|overlay|swarm|true", "1|xxxxxxxxxxxxxxxxxxxxxxxxx", False),
        ("underground|xxxxxxxxxxxxxxxxxxxxxxxxx|overlay|swarm|true", "1|different", False),
        (
            "underground|xxxxxxxxxxxxxxxxxxxxxxxxx|overlay|swarm|true",
            "2|xxxxxxxxxxxxxxxxxxxxxxxxx",
            False,
        ),
    ],
)
def test_pi_postactivation_requires_actual_reviewed_attachment(
    metadata: str,
    attachment: str,
    accepted: bool,
) -> None:
    tasks = read_yaml(ROLE / "tasks" / "activate.yml")
    gate = tasks[-1]
    assert gate["when"] == "not zabbix_agent_existing_project"
    up = next(task for task in tasks if task["name"].startswith("Reconcile only"))
    assert tasks.index(up) < tasks.index(gate)
    values = variables("PiThree") | {
        "zabbix_agent_attached_overlay": {"stdout": metadata},
        "zabbix_agent_attached_network": {"stdout": attachment},
    }
    environment = jinja2.Environment()  # noqa: S701 - evaluate fixed predicates, not HTML.
    assert (
        all(
            environment.compile_expression(expression)(**values)
            for expression in gate["ansible.builtin.assert"]["that"]
        )
        is accepted
    )


def test_activation_reconciles_one_service_and_never_writes_beast_compose() -> None:
    tasks = read_yaml(ROLE / "tasks" / "activate.yml")
    gating = tasks[0]["ansible.builtin.assert"]["that"]
    assert "homelab_allow_service_restart" in gating
    assert "zabbix_agent_maintenance_window_approved" in gating
    assert "zabbix_agent_version_compatibility_reviewed" in gating
    assert "zabbix_agent_central_identity_confirmed" in gating
    assert "zabbix_agent_existing_project or zabbix_agent_overlay_attachment_approved" in gating
    assert "not zabbix_agent_existing_project or zabbix_agent_canonical_integrated" in gating
    assert "not ansible_check_mode" in gating
    activation = next(task for task in tasks if task["name"].startswith("Reconcile only"))
    argv = activation["ansible.builtin.command"]["argv"]
    assert "'--no-deps'" in argv and "'--pull', 'never'" in argv and "'--no-build'" in argv
    assert "'down'" not in argv and "'restart'" not in argv and "'--force-recreate'" not in argv
    assert "zabbix_agent_service_name" in argv
    assert "when" not in activation  # Compose performs its own idempotent reconciliation.
    prepares = read_yaml(ROLE / "tasks" / "prepare.yml")
    templates = [task for task in prepares if "ansible.builtin.template" in task]
    assert all(task["ansible.builtin.template"]["backup"] for task in templates)
    compose = next(
        task for task in templates if task["ansible.builtin.template"]["src"] == "compose.yaml.j2"
    )
    assert compose["when"] == "not zabbix_agent_existing_project"
    assert (
        compose["ansible.builtin.template"]["dest"] == "{{ zabbix_agent_compose_dir }}/compose.yaml"
    )
    assert all(
        "zabbix_agent_canonical_compose" not in task["ansible.builtin.template"]["dest"]
        for task in templates
    )
    assert "compose.zabbix-agent.override.yaml" not in "\n".join(
        path.read_text() for path in ROLE.rglob("*") if path.is_file()
    )


@pytest.mark.parametrize("host", ["Controller", "PiOne"])
def test_compose_argv_has_exactly_one_authoritative_file(host: str) -> None:
    tasks = read_yaml(ROLE / "tasks" / "activate.yml")
    expression = next(task for task in tasks if "ansible.builtin.set_fact" in task)[
        "ansible.builtin.set_fact"
    ]["zabbix_agent_compose_argv"]
    environment = jinja2.Environment()  # noqa: S701 - evaluate fixed argv, never HTML.
    environment.filters["dirname"] = lambda path: str(Path(path).parent)
    argv = environment.compile_expression(expression.strip()[2:-2].strip())(**variables(host))
    assert isinstance(argv, list)
    assert argv.count("-f") == 1
    expected = (
        variables(host)["zabbix_agent_canonical_compose"]
        if host == "Controller"
        else "/etc/homelab/zabbix-agent/compose.yaml"
    )
    assert argv[argv.index("-f") + 1] == expected
    assert argv[argv.index("--project-name") + 1] == (
        "monitoring" if host == "Controller" else "zabbix-agent"
    )


def test_pi_cannot_inherit_benbeast_nfs_mounts(tmp_path: Path) -> None:
    values = variables() | {
        "zabbix_agent_filesystem_anchors": [
            {
                "alias": "nfs_docker",
                "source": "/mnt/nas/docker/anchors/capacity",
                "expected_mount": "/mnt/nas/docker",
                "expected_fstype": "nfs4",
            },
        ]
    }
    result = run_validation(tmp_path, values)
    assert result.returncode != 0
    assert "Inspect only agent container identity" not in result.stdout


def interim_beast_variables() -> dict[str, Any]:
    return variables("Controller") | {
        "zabbix_agent_image": "zabbix/zabbix-agent2:alpine-7.2.12",
        "zabbix_agent_image_digest": INTERIM_DIGEST,
        "zabbix_agent_expected_image_id": "sha256:" + "e" * 64,
        "zabbix_agent_expected_container_image_id": BEAST_IMAGE_ID,
    }


def test_beast_version_change_is_rejected_without_its_own_approval(tmp_path: Path) -> None:
    result = run_validation(tmp_path, interim_beast_variables())
    assert result.returncode != 0
    assert "Inspect only agent container identity" not in result.stdout


def test_explicit_interim_option_keeps_current_runtime_baseline_separate(tmp_path: Path) -> None:
    values = interim_beast_variables() | {"zabbix_agent_version_change_approved": True}
    result = run_validation(tmp_path, values)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "changed=0" in result.stdout
    assert values["zabbix_agent_version_compatibility_reviewed"] is False
    assert "Inspect only agent container identity" not in result.stdout
    inspect_tasks = read_yaml(ROLE / "tasks" / "inspect.yml")
    baseline = next(
        task for task in inspect_tasks if task["name"].startswith("Refuse a second agent")
    )
    assert "zabbix_agent_expected_container_image_id" in str(baseline)


def test_interim_version_approval_cannot_select_an_unreviewed_digest(tmp_path: Path) -> None:
    values = interim_beast_variables() | {
        "zabbix_agent_version_change_approved": True,
        "zabbix_agent_image_digest": "sha256:" + "f" * 64,
    }
    result = run_validation(tmp_path, values)
    assert result.returncode != 0
    assert "Inspect only agent container identity" not in result.stdout


@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker Compose CLI not installed")
@pytest.mark.parametrize(
    "service",
    ["zabbix-agent", "zabbix-agent-pironman", "zabbix-agent-zigbeepi", "zabbix-agent-loungeotbr"],
)
def test_selected_image_query_excludes_dependencies_and_does_not_resolve_env(
    tmp_path: Path,
    service: str,
) -> None:
    docker = shutil.which("docker")
    assert docker is not None
    image = "zabbix/zabbix-agent2:alpine-7.0.31@" + PI_DIGEST
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        yaml.safe_dump(
            {
                "services": {
                    service: {
                        "image": image,
                        "depends_on": ["zabbix-server"],
                        "env_file": ["./does-not-exist.env"],
                    },
                    "zabbix-server": {"image": "fixture/server:1"},
                    "unrelated": {"image": "fixture/unrelated:1"},
                }
            }
        )
    )
    wrapper = ROLE / "files" / "selected_compose_image.py"
    query = [
        docker,
        "compose",
        "--project-name",
        "fixture",
        "-f",
        str(compose),
        "--env-file",
        "/dev/null",
        "config",
        "--format",
        "json",
        "--no-interpolate",
        "--no-env-resolution",
        service,
    ]
    result = subprocess.run(
        [sys.executable, str(wrapper), *query],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [image]
    assert "fixture/server" not in result.stdout and "services" not in result.stdout

    # An interpolated image is never accepted even if an environment value could resolve it.
    content = yaml.safe_load(compose.read_text())
    content["services"][service]["image"] = "${SELECTED_AGENT_IMAGE}"
    compose.write_text(yaml.safe_dump(content))
    environment = os.environ.copy() | {"SELECTED_AGENT_IMAGE": image}
    rejected = subprocess.run(
        [sys.executable, str(wrapper), *query],
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
        check=False,
    )
    assert rejected.returncode != 0
    assert rejected.stdout == ""
    assert image not in rejected.stderr


def test_selected_canonical_image_is_read_only_and_checked_before_up() -> None:
    tasks = read_yaml(ROLE / "tasks" / "activate.yml")
    project = next(task for task in tasks if task["name"].startswith("Project only"))
    query = project["ansible.builtin.command"]["argv"]
    assert "'/usr/bin/python3', '-c'" in query
    assert "'--no-interpolate'" in query and "'--no-env-resolution'" in query
    assert "'--env-file', '/dev/null'" in query
    assert project["no_log"] is True and project["changed_when"] is False
    inspect_image = next(task for task in tasks if task["name"].startswith("Read the selected"))
    assert inspect_image["ansible.builtin.command"]["argv"][1:3] == ["image", "inspect"]
    assert inspect_image["changed_when"] is False and inspect_image["no_log"] is True
    check = next(task for task in tasks if task["name"].startswith("Reject a canonical image"))
    expression = check["ansible.builtin.assert"]["that"][0]
    environment = jinja2.Environment()  # noqa: S701 - evaluate an identity check, not HTML.
    evaluate = environment.compile_expression(expression)
    assert (
        evaluate(
            zabbix_agent_canonical_image_observed={"stdout": BEAST_IMAGE_ID},
            zabbix_agent_expected_image_id=BEAST_IMAGE_ID,
        )
        is True
    )
    assert (
        evaluate(
            zabbix_agent_canonical_image_observed={"stdout": BEAST_IMAGE_ID},
            zabbix_agent_expected_image_id="sha256:" + "e" * 64,
        )
        is False
    )
    up = next(task for task in tasks if task["name"].startswith("Reconcile only"))
    assert tasks.index(project) < tasks.index(inspect_image) < tasks.index(check) < tasks.index(up)

@pytest.mark.parametrize("contract", [
    {"zabbix_agent_admitted_hosts": []},
    {"zabbix_agent_admitted_hosts": ["Other"]},
    {"zabbix_agent_controller_host": "Other"},
    {"zabbix_agent_lazy_overlay_host": "Controller"},
])
def test_unreviewed_site_contract_refused_before_host_access(tmp_path, contract):
    result = run_validation(tmp_path, variables() | contract)
    assert result.returncode != 0
    assert "changed=0" in result.stdout
