from datetime import datetime, timezone

from pysysutils.health import HealthThresholds, evaluate_snapshot
from pysysutils.models import (
    BatteryHealthSnapshot,
    BatterySnapshot,
    BatteryStatusSnapshot,
    CpuSnapshot,
    DiskPartition,
    DiskSnapshot,
    HealthLevel,
    MemorySnapshot,
    NetworkSnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)


def _minimal_snapshot(**overrides) -> SystemSnapshot:
    base = SystemSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform="linux",
        hostname="test",
        cpu=CpuSnapshot(percent=10.0, per_cpu=None, count_logical=4, count_physical=2),
        memory=MemorySnapshot(1, 1, 1, 1, 50.0, None, None, None),
        disk=DiskSnapshot(partitions=[]),
        network=NetworkSnapshot(0, 0, None, None, None, None),
        battery=BatterySnapshot(
            status=BatteryStatusSnapshot(False, None, None, None, "n/a"),
            health=BatteryHealthSnapshot(False, None, None, None, None, None),
        ),
        top_processes=ProcessSnapshot(processes=[]),
        overall=HealthLevel.HEALTHY,
        issues=[],
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_memory_critical_sets_exit_code_2():
    from pysysutils.health import exit_code_for

    snap = _minimal_snapshot(
        memory=MemorySnapshot(1, 1, 1, 1, 96.0, None, None, None),
    )
    level, issues = evaluate_snapshot(snap, HealthThresholds())
    assert level == HealthLevel.CRITICAL
    assert issues
    assert exit_code_for(level) == 2


def test_memory_warning_sets_exit_code_1():
    from pysysutils.health import exit_code_for

    snap = _minimal_snapshot(
        memory=MemorySnapshot(1, 1, 1, 1, 86.0, None, None, None),
    )
    level, _ = evaluate_snapshot(snap, HealthThresholds())
    assert level == HealthLevel.WARNING
    assert exit_code_for(level) == 1


def test_no_battery_skipped_does_not_affect_overall():
    snap = _minimal_snapshot(
        cpu=CpuSnapshot(percent=10.0, per_cpu=None, count_logical=4, count_physical=2),
        battery=BatterySnapshot(
            status=BatteryStatusSnapshot(False, None, None, None, "n/a"),
            health=BatteryHealthSnapshot(False, None, None, None, None, None),
        ),
    )
    level, issues = evaluate_snapshot(snap, HealthThresholds())
    assert level == HealthLevel.HEALTHY
    assert issues == []


def test_low_battery_on_discharge_is_critical():
    snap = _minimal_snapshot(
        battery=BatterySnapshot(
            status=BatteryStatusSnapshot(True, 8.0, False, 600, "0h 10m"),
            health=BatteryHealthSnapshot(False, None, None, None, None, None),
        ),
    )
    level, issues = evaluate_snapshot(snap, HealthThresholds())
    assert level == HealthLevel.CRITICAL
    assert any("Battery charge" in issue for issue in issues)


def test_disk_critical_on_any_mount():
    snap = _minimal_snapshot(
        disk=DiskSnapshot(
            partitions=[
                DiskPartition("/dev/sda1", "/", "ext4", 100, 96, 4, 96.0),
            ]
        ),
    )
    level, _ = evaluate_snapshot(snap, HealthThresholds())
    assert level == HealthLevel.CRITICAL


def test_thresholds_from_cli_cpu_max():
    from pysysutils.health import thresholds_from_cli

    thresholds = thresholds_from_cli(cpu_max=90.0)
    assert thresholds.cpu_critical == 90.0
    assert thresholds.cpu_warning == 80.0
