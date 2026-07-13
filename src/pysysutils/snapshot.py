import socket
import sys
from datetime import datetime, timezone

from pysysutils.collectors.cpu import collect_cpu
from pysysutils.collectors.disk import collect_disk
from pysysutils.collectors.memory import collect_memory
from pysysutils.collectors.network import collect_network
from pysysutils.collectors.processes import collect_processes
from pysysutils.models import (
    BatteryHealthSnapshot,
    BatterySnapshot,
    BatteryStatusSnapshot,
    HealthLevel,
    SystemSnapshot,
)


def _battery_placeholder() -> BatterySnapshot:
    return BatterySnapshot(
        status=BatteryStatusSnapshot(False, None, None, None, "n/a"),
        health=BatteryHealthSnapshot(False, None, None, None, None, None),
    )


def build_snapshot(top: int = 10) -> SystemSnapshot:
    return SystemSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform=sys.platform,
        hostname=socket.gethostname(),
        cpu=collect_cpu(),
        memory=collect_memory(),
        disk=collect_disk(),
        network=collect_network(),
        battery=_battery_placeholder(),
        top_processes=collect_processes(top=top),
        overall=HealthLevel.HEALTHY,
        issues=[],
    )
