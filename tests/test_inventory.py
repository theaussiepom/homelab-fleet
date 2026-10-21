from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType


def load_inventory_checker() -> ModuleType:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts/check-inventory"
    loader = SourceFileLoader("check_inventory", str(script))
    spec = importlib.util.spec_from_loader("check_inventory", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_policy_script_passes(tmp_path: Path) -> None:
    module = load_inventory_checker()
    report = fixture_check(module, tmp_path)
    assert report["ok"], report["errors"]


def test_observer_release_is_exactly_pinned(tmp_path: Path) -> None:
    module = load_inventory_checker()
    report = fixture_check(module, tmp_path, include_secret_scan=False)
    checks = report["checks"]
    assert checks["observer_version"] == "0.1.0"
    assert checks["observer_version"] in checks["observer_release_url"]
    assert len(checks["observer_sha256"]) == 64


def test_no_observer_python_source_exists_in_fleet() -> None:
    module = load_inventory_checker()
    assert module.scan_observer_source_boundaries() == []


def test_every_role_has_tasks() -> None:
    root = Path(__file__).resolve().parents[1]
    required = {
        "fleet_identity",
        "fleet_admission",
        "fleet_network_stage",
        "nfs_docker",
        "code_tunnel",
        "pi_telemetry",
        "host_config_backup",
        "otbr_watchdog",
        "observer_access",
        "observer_probe_agent",
        "observer_gateway",
        "zabbix_agent",
    }
    assert {path.name for path in (root / "roles").iterdir()} == required
    assert all((root / "roles" / role / "tasks/main.yml").exists() for role in required)


def fixture_check(module, tmp_path, **kwargs):
    from catalog_fixture import CATALOG
    from fleet_catalog import load_catalog, project
    destination = tmp_path / "inventory"
    project(load_catalog(CATALOG), destination)
    return module.check(catalog_path=CATALOG, inventory_dir=destination, **kwargs)
