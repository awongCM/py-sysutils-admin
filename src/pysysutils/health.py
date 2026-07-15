from __future__ import annotations

from dataclasses import dataclass, replace

from pysysutils.models import HealthLevel, SystemSnapshot


@dataclass
class HealthThresholds:
    cpu_warning: float = 85.0
    cpu_critical: float = 95.0
    mem_warning: float = 85.0
    mem_critical: float = 95.0
    disk_warning: float = 85.0
    disk_critical: float = 95.0
    swap_warning: float = 70.0
    swap_critical: float = 90.0
    battery_charge_warning: float = 20.0
    battery_charge_critical: float = 10.0
    battery_health_warning: float = 80.0
    battery_health_critical: float = 60.0
    battery_min_floor: float | None = None


def _level_for_high(value: float, warning: float, critical: float) -> HealthLevel:
    if value >= critical:
        return HealthLevel.CRITICAL
    if value >= warning:
        return HealthLevel.WARNING
    return HealthLevel.HEALTHY


def _level_for_low(value: float, warning: float, critical: float) -> HealthLevel:
    if value <= critical:
        return HealthLevel.CRITICAL
    if value <= warning:
        return HealthLevel.WARNING
    return HealthLevel.HEALTHY


def _battery_charge_level(percent: float, thresholds: HealthThresholds) -> HealthLevel:
    if thresholds.battery_min_floor is not None:
        if percent >= thresholds.battery_min_floor:
            return HealthLevel.HEALTHY
        return HealthLevel.CRITICAL
    return _level_for_low(
        percent,
        thresholds.battery_charge_warning,
        thresholds.battery_charge_critical,
    )


def _max_level(*levels: HealthLevel) -> HealthLevel:
    order = {HealthLevel.HEALTHY: 0, HealthLevel.WARNING: 1, HealthLevel.CRITICAL: 2, HealthLevel.SKIPPED: -1}
    active = [level for level in levels if level != HealthLevel.SKIPPED]
    if not active:
        return HealthLevel.HEALTHY
    return max(active, key=lambda level: order[level])


def evaluate_snapshot(snap: SystemSnapshot, thresholds: HealthThresholds) -> tuple[HealthLevel, list[str]]:
    levels: list[HealthLevel] = []
    issues: list[str] = []

    cpu_level = _level_for_high(snap.cpu.percent, thresholds.cpu_warning, thresholds.cpu_critical)
    levels.append(cpu_level)
    if cpu_level != HealthLevel.HEALTHY:
        issues.append(
            f"CPU usage at {snap.cpu.percent:.1f}% ({cpu_level.value} threshold: "
            f"{thresholds.cpu_critical if cpu_level == HealthLevel.CRITICAL else thresholds.cpu_warning}%)"
        )

    mem_level = _level_for_high(snap.memory.percent, thresholds.mem_warning, thresholds.mem_critical)
    levels.append(mem_level)
    if mem_level != HealthLevel.HEALTHY:
        issues.append(
            f"Memory usage at {snap.memory.percent:.1f}% ({mem_level.value} threshold: "
            f"{thresholds.mem_critical if mem_level == HealthLevel.CRITICAL else thresholds.mem_warning}%)"
        )

    if snap.memory.swap_percent is not None:
        swap_level = _level_for_high(snap.memory.swap_percent, thresholds.swap_warning, thresholds.swap_critical)
        levels.append(swap_level)
        if swap_level != HealthLevel.HEALTHY:
            issues.append(
                f"Swap usage at {snap.memory.swap_percent:.1f}% ({swap_level.value} threshold: "
                f"{thresholds.swap_critical if swap_level == HealthLevel.CRITICAL else thresholds.swap_warning}%)"
            )

    for part in snap.disk.partitions:
        disk_level = _level_for_high(part.percent, thresholds.disk_warning, thresholds.disk_critical)
        levels.append(disk_level)
        if disk_level != HealthLevel.HEALTHY:
            issues.append(
                f"Disk {part.mountpoint} at {part.percent:.1f}% ({disk_level.value} threshold: "
                f"{thresholds.disk_critical if disk_level == HealthLevel.CRITICAL else thresholds.disk_warning}%)"
            )

    if snap.battery.status.present:
        if snap.battery.status.percent is not None and snap.battery.status.power_plugged is not True:
            bat_level = _battery_charge_level(snap.battery.status.percent, thresholds)
            levels.append(bat_level)
            if bat_level != HealthLevel.HEALTHY:
                threshold = (
                    thresholds.battery_min_floor
                    if thresholds.battery_min_floor is not None
                    else (
                        thresholds.battery_charge_critical
                        if bat_level == HealthLevel.CRITICAL
                        else thresholds.battery_charge_warning
                    )
                )
                issues.append(
                    f"Battery charge at {snap.battery.status.percent:.0f}% ({bat_level.value} threshold: {threshold}%)"
                )

        if snap.battery.health.available and snap.battery.health.health_percent is not None:
            health_level = _level_for_low(
                snap.battery.health.health_percent,
                thresholds.battery_health_warning,
                thresholds.battery_health_critical,
            )
            levels.append(health_level)
            if health_level != HealthLevel.HEALTHY:
                issues.append(
                    f"Battery health at {snap.battery.health.health_percent:.0f}% ({health_level.value} threshold: "
                    f"{thresholds.battery_health_critical if health_level == HealthLevel.CRITICAL else thresholds.battery_health_warning}%)"
                )
    else:
        levels.append(HealthLevel.SKIPPED)

    overall = _max_level(*levels)
    return overall, issues


def exit_code_for(level: HealthLevel) -> int:
    return {HealthLevel.HEALTHY: 0, HealthLevel.WARNING: 1, HealthLevel.CRITICAL: 2}.get(level, 1)


def thresholds_from_cli(
    cpu_max: float | None = None,
    mem_max: float | None = None,
    disk_max: float | None = None,
    battery_min: float | None = None,
    battery_health_min: float | None = None,
) -> HealthThresholds:
    thresholds = HealthThresholds()
    if cpu_max is not None:
        thresholds = replace(thresholds, cpu_critical=cpu_max, cpu_warning=max(cpu_max - 10, 0))
    if mem_max is not None:
        thresholds = replace(thresholds, mem_critical=mem_max, mem_warning=max(mem_max - 10, 0))
    if disk_max is not None:
        thresholds = replace(thresholds, disk_critical=disk_max, disk_warning=max(disk_max - 10, 0))
    if battery_min is not None:
        thresholds = replace(
            thresholds,
            battery_charge_critical=battery_min,
            battery_charge_warning=min(battery_min + 10, 100),
            battery_min_floor=battery_min,
        )
    if battery_health_min is not None:
        thresholds = replace(
            thresholds,
            battery_health_critical=battery_health_min,
            battery_health_warning=min(battery_health_min + 10, 100),
        )
    return thresholds
