from __future__ import annotations

import re
import subprocess

from pysysutils.collectors.battery_health.base import BatteryHealthBackend
from pysysutils.models import BatteryHealthSnapshot

IOREG_CMD = ["ioreg", "-r", "-c", "AppleSmartBattery"]
SUBPROCESS_TIMEOUT = 5
_NOOP = BatteryHealthSnapshot(False, None, None, None, None, None)


def _parse_ioreg_output(text: str) -> BatteryHealthSnapshot:
    fields: dict[str, int] = {}
    for match in re.finditer(r'"(\w+)"\s*=\s*(\d+)', text):
        fields[match.group(1)] = int(match.group(2))

    design = fields.get("DesignCapacity")
    full = fields.get("MaxCapacity")
    cycle_count = fields.get("CycleCount")

    if not design or not full or design <= 0:
        return _NOOP

    health_percent = round((full / design) * 100, 1)
    condition = None
    if health_percent <= 60:
        condition = "Service Recommended"
    elif health_percent <= 80:
        condition = "Replace Soon"

    # ioreg reports mAh; capacity fields left None to avoid mislabeled units.
    return BatteryHealthSnapshot(
        available=True,
        health_percent=health_percent,
        cycle_count=cycle_count,
        design_capacity_mwh=None,
        full_charge_capacity_mwh=None,
        condition=condition,
    )


class DarwinBatteryHealthBackend(BatteryHealthBackend):
    def collect(self) -> BatteryHealthSnapshot:
        try:
            result = subprocess.run(
                IOREG_CMD,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return _NOOP

        if result.returncode != 0 or not result.stdout:
            return _NOOP

        return _parse_ioreg_output(result.stdout)
