import socket
import sys
from datetime import datetime, timezone

from pysysutils.collectors.battery_health import collect_battery_health
from pysysutils.collectors.battery_status import collect_battery_status
from pysysutils.collectors.cpu import collect_cpu
from pysysutils.collectors.disk import collect_disk
from pysysutils.collectors.memory import collect_memory
from pysysutils.collectors.network import collect_network
from pysysutils.collectors.processes import collect_processes
from pysysutils.health import HealthThresholds, evaluate_snapshot
from pysysutils.models import (
    BatteryHealthSnapshot,
    BatterySnapshot,
    HealthLevel,
    SystemSnapshot,
)


def _collect_battery(include_health: bool = True) -> BatterySnapshot:
    return BatterySnapshot(
        status=collect_battery_status(),
        health=collect_battery_health() if include_health else BatteryHealthSnapshot(
            False, None, None, None, None, None
        ),
    )


def build_snapshot(top: int = 10, include_battery_health: bool = True) -> SystemSnapshot:
    snap = SystemSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform=sys.platform,
        hostname=socket.gethostname(),
        cpu=collect_cpu(),
        memory=collect_memory(),
        disk=collect_disk(),
        network=collect_network(),
        battery=_collect_battery(include_health=include_battery_health),
        top_processes=collect_processes(top=top),
        overall=HealthLevel.HEALTHY,
        issues=[],
    )
    overall, issues = evaluate_snapshot(snap, HealthThresholds())
    snap.overall = overall
    snap.issues = issues
    return snap
