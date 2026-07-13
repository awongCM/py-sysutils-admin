import json
from io import StringIO
from datetime import datetime, timezone

from rich.console import Console
from pysysutils.models import (
    BatteryHealthSnapshot,
    BatterySnapshot,
    BatteryStatusSnapshot,
    CpuSnapshot,
    DiskSnapshot,
    HealthLevel,
    MemorySnapshot,
    NetworkSnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)
from pysysutils.formatters.json_fmt import to_json
from pysysutils.formatters.table import render_snapshot


def test_to_json_cpu_snapshot():
    snap = CpuSnapshot(percent=10.0, per_cpu=None, count_logical=4, count_physical=2)
    out = to_json(snap)
    data = json.loads(out)
    assert data["percent"] == 10.0


def test_render_snapshot_writes_cpu():
    snap = SystemSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform="linux",
        hostname="test",
        cpu=CpuSnapshot(percent=50.0, per_cpu=None, count_logical=4, count_physical=2),
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
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    render_snapshot(snap, console=console)
    out = buf.getvalue()
    assert "CPU" in out
    assert "50" in out
