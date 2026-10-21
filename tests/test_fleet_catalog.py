"""Projection checks run only against synthetic files in pytest temp directories."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog_fixture import CATALOG
from fleet_catalog import load_catalog, project, verify_projection
from test_inventory import load_inventory_checker


def test_exact_projection_and_policy_roundtrip(tmp_path: Path) -> None:
    catalog = load_catalog(CATALOG)
    output = tmp_path / "inventory"
    assert project(catalog, output)["host_commands"] == 0
    contract = verify_projection(catalog, output)
    assert contract["deployment_admitted"] is False
    assert output.stat().st_mode & 0o777 == 0o700
    assert all(p.stat().st_mode & 0o777 == 0o600 for p in output.rglob("*") if p.is_file())
    result = load_inventory_checker().check(
        catalog_path=CATALOG, inventory_dir=output, include_secret_scan=False
    )
    assert result["ok"], result["errors"]


@pytest.mark.parametrize("change", ["edit", "extra", "missing", "symlink", "policy"])
def test_projection_changes_refused(tmp_path: Path, change: str) -> None:
    catalog = load_catalog(CATALOG)
    output = tmp_path / "inventory"
    project(catalog, output)
    leaf = output / "hosts.yml"
    if change == "edit":
        leaf.write_text(leaf.read_text() + "\n# altered\n")
    elif change == "extra":
        (output / "extra.yml").write_text("{}")
    elif change == "missing":
        leaf.unlink()
    elif change == "symlink":
        saved = tmp_path / "saved.yml"
        saved.write_bytes(leaf.read_bytes())
        leaf.unlink()
        leaf.symlink_to(saved)
    else:
        catalog["fleet_management"]["policy"]["otbr_hosts"] = []
    with pytest.raises(ValueError):
        verify_projection(catalog, output)


@pytest.mark.parametrize(
    "change", ["path", "admitted", "flag", "unknown_host", "missing_hostvars", "pi_mismatch"]
)
def test_bad_catalog_refused_before_writing(tmp_path: Path, change: str) -> None:
    catalog = load_catalog(CATALOG)
    block = catalog["fleet_management"]
    files = block["inventory"]
    if change == "path":
        files["../escape.yml"] = {}
    elif change == "admitted":
        block["deployment_admitted"] = True
    elif change == "flag":
        files["group_vars/all.yml"]["homelab_allow_reboot"] = True
    elif change == "unknown_host":
        files["hosts.yml"]["all"]["children"]["docker_hosts"]["hosts"]["Unknown"] = {}
    elif change == "missing_hostvars":
        files.pop("host_vars/Controller.yml")
    else:
        files["hosts.yml"]["all"]["children"]["physical_pis"]["hosts"] = {}
    output = tmp_path / "inventory"
    with pytest.raises(ValueError):
        project(catalog, output)
    assert not output.exists()


def test_changed_nfs_pair_fails_even_with_self_consistent_projection(tmp_path: Path) -> None:
    catalog = load_catalog(CATALOG)
    catalog["fleet_management"]["inventory"]["host_vars/Controller.yml"]["nfs_boot_mounts"][0][
        "source"
    ] = "wrong.example.invalid:/export"
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog))
    output = tmp_path / "inventory"
    project(catalog, output)
    result = load_inventory_checker().check(
        catalog_path=catalog_path, inventory_dir=output, include_secret_scan=False
    )
    assert not result["ok"]
    assert any("incorrect primary NFS" in error for error in result["errors"])


def test_no_implicit_production_inventory() -> None:
    with pytest.raises(ValueError, match="explicit catalog"):
        load_inventory_checker().check(include_secret_scan=False)


def test_duplicate_catalog_keys_refused(tmp_path: Path) -> None:
    source = tmp_path / "duplicate.json"
    source.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="duplicate"):
        load_catalog(source)


def test_existing_destination_preserved(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    marker.write_text("preserve")
    with pytest.raises(ValueError, match="must be new"):
        project(load_catalog(CATALOG), tmp_path)
    assert marker.read_text() == "preserve"


@pytest.mark.parametrize(
    "name,mode",
    [
        (".", 0o755),
        ("group_vars", 0o750),
        ("hosts.yml", 0o644),
        ("projection.json", 0o640),
        ("host_vars/Controller.yml", 0o660),
        ("hosts.yml", 0o4600),
    ],
)
def test_projection_permission_changes_refused_before_admission(
    tmp_path: Path, name: str, mode: int
) -> None:
    catalog = load_catalog(CATALOG)
    output = tmp_path / "inventory"
    project(catalog, output)
    target = output / name
    original = target.stat().st_mode & 0o7777
    target.chmod(mode)
    if target.stat().st_mode & 0o7777 != mode:
        target.chmod(original)
        pytest.skip("Filesystem did not retain the requested special mode bits")
    try:
        with pytest.raises(ValueError, match="permissions"):
            verify_projection(catalog, output)
        with pytest.raises(ValueError, match="permissions"):
            load_inventory_checker().check(
                catalog_path=CATALOG, inventory_dir=output, include_secret_scan=False
            )
        assert target.stat().st_mode & 0o7777 == mode
    finally:
        target.chmod(original)
