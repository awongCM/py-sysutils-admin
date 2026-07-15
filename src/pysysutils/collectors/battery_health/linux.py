from __future__ import annotations

from pathlib import Path

from pysysutils.collectors.battery_health.base import BatteryHealthBackend
from pysysutils.models import BatteryHealthSnapshot

SYSFS_ROOT = Path("/sys/class/power_supply")
_NOOP = BatteryHealthSnapshot(False, None, None, None, None, None)


def _sysfs_root() -> Path:
    return SYSFS_ROOT


def _read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def _collect_from_dir(bat_dir: Path) -> BatteryHealthSnapshot | None:
    design_uwh = _read_int(bat_dir / "energy_full_design")
    full_uwh = _read_int(bat_dir / "energy_full")
    if design_uwh is None or full_uwh is None or design_uwh <= 0:
        charge_design = _read_int(bat_dir / "charge_full_design")
        charge_full = _read_int(bat_dir / "charge_full")
        if charge_design and charge_full and charge_design > 0:
            health_percent = round((charge_full / charge_design) * 100, 1)
            return BatteryHealthSnapshot(
                available=True,
                health_percent=health_percent,
                cycle_count=_read_int(bat_dir / "cycle_count"),
                design_capacity_mwh=None,
                full_charge_capacity_mwh=None,
                condition=None,
            )
        return None

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


class LinuxBatteryHealthBackend(BatteryHealthBackend):
    def collect(self) -> BatteryHealthSnapshot:
        root = _sysfs_root()
        if not root.is_dir():
            return _NOOP

        best: BatteryHealthSnapshot | None = None
        for bat_dir in sorted(root.glob("BAT*")):
            snap = _collect_from_dir(bat_dir)
            if snap is None:
                continue
            if best is None or (
                snap.health_percent is not None
                and (best.health_percent is None or snap.health_percent < best.health_percent)
            ):
                best = snap

        return best if best is not None else _NOOP
