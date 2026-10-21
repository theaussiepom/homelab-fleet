"""Project one literal image reference; never emit the internal Compose model.

Invoked as fixed Python -c source by the gated role: no installed helper or new
package. Compose interpolation and env-file resolution must both be disabled.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

QUERY_SUFFIX = [
    "--env-file",
    "/dev/null",
    "config",
    "--format",
    "json",
    "--no-interpolate",
    "--no-env-resolution",
]
AGENT_SERVICES = {
    "zabbix-agent",
    "zabbix-agent-pironman",
    "zabbix-agent-zigbeepi",
    "zabbix-agent-loungeotbr",
}
PINNED_AGENT_IMAGE = re.compile(
    r"(?:sha256:[0-9a-f]{64}|"
    r"zabbix/zabbix-agent2(?::[A-Za-z0-9_.-]+)?@sha256:[0-9a-f]{64})"
)


def main(argv: list[str]) -> int:
    if (
        len(argv) <= len(QUERY_SUFFIX)
        or argv[-len(QUERY_SUFFIX) - 1 : -1] != QUERY_SUFFIX
        or argv[-1] not in AGENT_SERVICES
    ):
        print("Selected-image query requires its fixed nonresolving options.", file=sys.stderr)
        return 2
    try:
        result = subprocess.run(argv, capture_output=True, timeout=20, check=False)
        if result.returncode or len(result.stdout) > 2 * 1024 * 1024:
            raise ValueError("config unavailable or oversized")
        model = json.loads(result.stdout)
        image = model["services"][argv[-1]]["image"]
        if not isinstance(image, str) or not PINNED_AGENT_IMAGE.fullmatch(image):
            raise ValueError("image must be a literal approved-repository digest or local image ID")
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
        # Never propagate raw model, subprocess output, paths or parser errors.
        print(
            "Could not verify a literal pinned image for the selected agent service.",
            file=sys.stderr,
        )
        return 2
    print(image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
