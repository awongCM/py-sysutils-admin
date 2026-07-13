from __future__ import annotations

from pathlib import Path

from pysysutils.collectors.battery_health.base import BatteryHealthBackend
from pysysutils.models import BatteryHealthSnapshot

SYSFS_ROOT = Path("/sys/class/power_supply")


def _sysfs_root() -> Path:
    return SYSFS_ROOT


def _read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


class LinuxBatteryHealthBackend(BatteryHealthBackend):
    def collect(self) -> BatteryHealthSnapshot:
        root = _sysfs_root()
        if not root.is_dir():
            return BatteryHealthSnapshot(False, None, None, None, None, None)

        for bat_dir in sorted(root.glob("BAT*")):
            design_uwh = _read_int(bat_dir / "energy_full_design")
            full_uwh = _read_int(bat_dir / "energy_full")
            if design_uwh is None or full_uwh is None or design_uwh <= 0:
                charge_full = _read_int(bat_dir / "charge_full_design")
                charge_now = _read_int(bat_dir / "charge_full")
                if charge_full and charge_now and charge_full > 0:
                    health_percent = round((charge_now / charge_full) * 100, 1)
                    return BatteryHealthSnapshot(
                        available=True,
                        health_percent=health_percent,
                        cycle_count=_read_int(bat_dir / "cycle_count"),
                        design_capacity_mwh=None,
                        full_charge_capacity_mwh=None,
                        condition=None,
                    )
                continue

            design_mwh = design_uwh // 1000
            full_mwh = full_uwh // 1000
            health_percent = round((full_uwh / design_uwh) * 100, 1)
            return BatteryHealthSnapshot(
                available=True,
                health_percent=health_percent,
                cycle_count=_read_int(bat_dir / "cycle_count"),
                design_capacity_mwh=design_mwh,
                full_charge_capacity_mwh=full_mwh,
                condition=None,
            )

        return BatteryHealthSnapshot(False, None, None, None, None, None)
