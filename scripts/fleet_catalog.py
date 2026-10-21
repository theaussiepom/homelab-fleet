"""Project fleet policy from one site catalog; never contact managed hosts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ('managed_hosts', 'docker_hosts', 'raspberry_pis', 'telemetry_hosts',
          'backup_hosts', 'code_tunnel_hosts', 'observer_hosts', 'otbr_hosts',
          'observer_gateway', 'physical_pis')


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def load_catalog(path: Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate catalog key')
            result[key] = value
        return result
    value = json.loads(path.read_text(), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError('catalog must be an object')
    return value


def materialize(catalog: dict[str, Any]) -> dict[str, bytes]:
    if catalog.get('schema_version') != 1 or catalog.get('site', {}).get('environment') not in ('synthetic', 'production'):
        raise ValueError('unsupported site catalog')
    block = catalog.get('fleet_management')
    if not isinstance(block, dict) or block.get('deployment_admitted') is not False:
        raise ValueError('explicit unadmitted fleet management policy required')
    files, policy = block.get('inventory'), block.get('policy')
    if not isinstance(files, dict) or not isinstance(policy, dict):
        raise ValueError('fleet inventory and policy must be objects')
    if not {'hosts.yml', 'group_vars/all.yml'} <= files.keys():
        raise ValueError('fleet inventory is incomplete')
    if set(policy) != {'managed_hosts', 'otbr_hosts', 'observer_gateway', 'primary_nfs'}:
        raise ValueError('exact fleet policy fields required')
    for key in ('managed_hosts', 'otbr_hosts', 'observer_gateway'):
        values = policy[key]
        if not isinstance(values, list) or len(values) != len(set(values)) or not all(
            isinstance(v, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', v) for v in values
        ):
            raise ValueError('invalid fleet policy membership')
    managed = set(policy['managed_hosts'])
    if not managed or not set(policy['otbr_hosts']) <= managed or len(policy['observer_gateway']) != 1 or not set(policy['observer_gateway']) <= managed:
        raise ValueError('invalid fleet policy scope')
    children = files['hosts.yml']['all']['children']
    if not set(GROUPS) <= children.keys():
        raise ValueError('fleet groups are incomplete')
    for group in GROUPS:
        if not isinstance(children[group].get('hosts'), dict) or not set(children[group]['hosts']) <= managed:
            raise ValueError('fleet group contains an unreviewed host')
    for key in ('managed_hosts', 'otbr_hosts', 'observer_gateway'):
        if set(children[key]['hosts']) != set(policy[key]):
            raise ValueError('fleet group differs from reviewed policy')
    if set(children['physical_pis']['hosts']) != set(children['raspberry_pis']['hosts']):
        raise ValueError('Pi groups disagree')
    if set(policy['primary_nfs']) != managed:
        raise ValueError('primary NFS policy is incomplete')
    for host in managed:
        if f'host_vars/{host}.yml' not in files:
            raise ValueError('host variables are incomplete')
        pair = policy['primary_nfs'][host]
        if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(v, str) and v for v in pair):
            raise ValueError('invalid primary NFS policy')

    def check_flags(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if (key.startswith('homelab_allow_') or key in ('homelab_retire_legacy_backup', 'fleet_profile_stage_admitted')) and item is not False:
                    raise ValueError('fleet mutation flags must remain false')
                check_flags(item)
        elif isinstance(value, list):
            for item in value:
                check_flags(item)

    if 'zabbix.yml' in files:
        for values in (files['group_vars/all.yml'], files['zabbix.yml']['all'].get('vars', {})):
            if set(values.get('zabbix_agent_admitted_hosts', [])) != managed:
                raise ValueError('Zabbix membership differs from reviewed fleet policy')
            controller = values.get('zabbix_agent_controller_host')
            lazy = values.get('zabbix_agent_lazy_overlay_host')
            if controller not in managed or lazy not in managed or controller == lazy:
                raise ValueError('Zabbix host roles are incomplete')
            node = values.get('zabbix_agent_admitted_lazy_overlay_swarm_node_id')
            if not isinstance(node, str) or not re.fullmatch(r'[a-z0-9]{25}', node):
                raise ValueError('Zabbix lazy-overlay node identity is required')

    output = {}
    for name, value in files.items():
        if not re.fullmatch(r'(?:hosts|zabbix)\.yml|(?:group_vars|host_vars)/[A-Za-z0-9_.-]+\.yml', name) or not isinstance(value, dict):
            raise ValueError('invalid fleet inventory file')
        check_flags(value)
        output[name] = yaml.safe_dump(value, sort_keys=False).encode()
    contract = {'format': 'homelab-fleet-projection-v1',
                'catalog_sha256': hashlib.sha256(canonical(catalog)).hexdigest(),
                'deployment_admitted': False, 'policy': policy,
                'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in output.items()}}
    output['projection.json'] = canonical(contract)
    return output


def project(catalog: dict[str, Any], destination: Path) -> dict[str, Any]:
    output = materialize(catalog)
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('projection destination must be new')
    if catalog['site']['environment'] == 'production' and destination.resolve().is_relative_to(ROOT):
        raise ValueError('production inventory must stay outside the public fleet checkout')
    destination.mkdir(mode=0o700)
    for name, raw in output.items():
        path = destination / name
        path.parent.mkdir(mode=0o700, exist_ok=True)
        with path.open('xb') as stream:
            path.chmod(0o600)
            stream.write(raw)
    return {'files': len(output), 'deployment_admitted': False, 'host_commands': 0}


def verify_projection(catalog: dict[str, Any], directory: Path) -> dict[str, Any]:
    expected = materialize(catalog)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('inventory directory must be a real directory')
    observed = set()
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError('inventory symlink refused')
        if path.is_file():
            observed.add(str(path.relative_to(directory)))
    if observed != set(expected):
        raise ValueError('inventory file set differs from catalog')
    for name, raw in expected.items():
        if (directory / name).read_bytes() != raw:
            raise ValueError('inventory bytes differ from catalog')
    return cast(dict[str, Any], json.loads(expected['projection.json']))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(project(load_catalog(args.catalog), args.out)))
        return 0
    except (ValueError, OSError, KeyError, TypeError):
        print(json.dumps({'refused': True, 'reason': 'invalid or incomplete catalog/projection destination'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
