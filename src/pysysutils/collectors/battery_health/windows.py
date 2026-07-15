from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from pysysutils.collectors.battery_health.base import BatteryHealthBackend
from pysysutils.models import BatteryHealthSnapshot

SUBPROCESS_TIMEOUT = 5
_NOOP = BatteryHealthSnapshot(False, None, None, None, None, None)


def _parse_battery_report(html: str) -> BatteryHealthSnapshot:
    design_match = re.search(r"DESIGN\s+CAPACITY[\s\S]*?([\d,]+)\s*mWh", html, re.I)
    full_match = re.search(r"FULL\s+CHARGE\s+CAPACITY[\s\S]*?([\d,]+)\s*mWh", html, re.I)
    cycle_match = re.search(r"CYCLE\s+COUNT[\s\S]*?([\d,]+)", html, re.I)

    if not design_match or not full_match:
        return _NOOP

    design_mwh = int(design_match.group(1).replace(",", ""))
    full_mwh = int(full_match.group(1).replace(",", ""))
    cycle_count = int(cycle_match.group(1).replace(",", "")) if cycle_match else None

    if design_mwh <= 0:
        return _NOOP

    health_percent = round((full_mwh / design_mwh) * 100, 1)
    return BatteryHealthSnapshot(
        available=True,
        health_percent=health_percent,
        cycle_count=cycle_count,
        design_capacity_mwh=design_mwh,
        full_charge_capacity_mwh=full_mwh,
        condition=None,
    )


class WindowsBatteryHealthBackend(BatteryHealthBackend):
    def collect(self) -> BatteryHealthSnapshot:
        output_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
                output_path = Path(tmp.name)
            result = subprocess.run(
                ["powercfg", "/batteryreport", "/output", str(output_path)],
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT,
                check=False,
            )
            if result.returncode != 0 or not output_path.exists():
                return _NOOP
            html = output_path.read_text(encoding="utf-8", errors="replace")
            return _parse_battery_report(html)
        except (OSError, subprocess.TimeoutExpired):
            return _NOOP
        finally:
            if output_path is not None:
                try:
                    output_path.unlink(missing_ok=True)
                except OSError:
                    pass
