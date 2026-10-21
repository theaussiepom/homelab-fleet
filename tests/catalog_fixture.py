"""Synthetic policy only; historical production receipts stay private."""
import copy
import json
from pathlib import Path
CATALOG = Path(__file__).resolve().parents[1] / "examples/fleet-catalog.json"
def inventory_data(name):
    return copy.deepcopy(json.loads(CATALOG.read_text())["fleet_management"]["inventory"][name])
