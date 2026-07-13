# PySysUtils Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `pysysutils`, a cross-platform machine health monitor with interactive CLI, JSON output, battery health, and automation-friendly `check` command (Option C).

**Architecture:** Modular collectors return dataclass snapshots via psutil; platform-specific battery health backends; Typer CLI + Rich formatters for humans; HealthEvaluator for thresholds and exit codes.

**Tech Stack:** Python 3.10+, psutil, Typer, Rich, pytest, pytest-mock

**Design spec:** `docs/superpowers/specs/2026-07-13-pysysutils-modernization-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | Package metadata, dependencies, console script |
| `src/pysysutils/__init__.py` | Version string |
| `src/pysysutils/models.py` | All dataclass snapshots + `to_dict()` |
| `src/pysysutils/collectors/cpu.py` | CPU metrics |
| `src/pysysutils/collectors/memory.py` | RAM + swap |
| `src/pysysutils/collectors/processes.py` | Process list |
| `src/pysysutils/collectors/disk.py` | Partition usage via psutil |
| `src/pysysutils/collectors/network.py` | Network counters + rates |
| `src/pysysutils/collectors/battery_status.py` | psutil battery status |
| `src/pysysutils/collectors/battery_health/*.py` | Platform health backends |
| `src/pysysutils/health.py` | Threshold evaluation + exit codes |
| `src/pysysutils/formatters/table.py` | Rich human output |
| `src/pysysutils/formatters/json_fmt.py` | JSON serialization |
| `src/pysysutils/cli.py` | Typer commands |
| `tests/*` | Unit + CLI tests |

---

## Phase 1 — Foundation

### Task 1: Package scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/pysysutils/__init__.py`
- Create: `src/pysysutils/__main__.py`
- Create: `tests/conftest.py` (empty placeholder)

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pysysutils"
version = "0.1.0"
description = "Cross-platform machine health monitor"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = [
    "psutil>=5.9.0",
    "typer>=0.12.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.0",
]

[project.scripts]
pysysutils = "pysysutils.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/pysysutils"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create `src/pysysutils/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Create `src/pysysutils/__main__.py`**

```python
from pysysutils.cli import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Install editable and verify**

Run: `pip install -e ".[dev]"`
Expected: Successful install with no errors

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/pysysutils/__init__.py src/pysysutils/__main__.py tests/conftest.py
git commit -m "chore: scaffold pysysutils package"
```

---

### Task 2: Data models

**Files:**
- Create: `src/pysysutils/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing test for HealthLevel and CpuSnapshot**

```python
# tests/test_models.py
from pysysutils.models import HealthLevel, CpuSnapshot


def test_cpu_snapshot_to_dict():
    snap = CpuSnapshot(percent=42.5, per_cpu=[10.0, 20.0], count_logical=4, count_physical=2)
    d = snap.to_dict()
    assert d["percent"] == 42.5
    assert d["count_logical"] == 4
    assert d["per_cpu"] == [10.0, 20.0]


def test_health_level_values():
    assert HealthLevel.HEALTHY.value == "healthy"
    assert HealthLevel.CRITICAL.value == "critical"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: pysysutils.models`

- [ ] **Step 3: Implement `models.py`**

Implement all dataclasses from design spec §5:
- `HealthLevel` enum
- `CpuSnapshot`, `MemorySnapshot`, `ProcessInfo`, `ProcessSnapshot`
- `DiskPartition`, `DiskSnapshot`, `NetworkSnapshot`
- `BatteryStatusSnapshot`, `BatteryHealthSnapshot`, `BatterySnapshot`
- `SystemSnapshot`

Each dataclass gets a `to_dict()` that returns JSON-serializable primitives (`datetime` → ISO string).

```python
# src/pysysutils/models.py (excerpt — implement full file per spec)
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any


class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    SKIPPED = "skipped"


@dataclass
class CpuSnapshot:
    percent: float
    per_cpu: list[float] | None
    count_logical: int
    count_physical: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

Repeat pattern for all models. `SystemSnapshot.to_dict()` must include `"schema_version": "1.0"`.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/models.py tests/test_models.py
git commit -m "feat: add snapshot data models"
```

---

### Task 3: CPU collector

**Files:**
- Create: `src/pysysutils/collectors/__init__.py`
- Create: `src/pysysutils/collectors/base.py`
- Create: `src/pysysutils/collectors/cpu.py`
- Create: `tests/test_cpu.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cpu.py
from pysysutils.collectors.cpu import collect_cpu


def test_collect_cpu(mocker):
    mocker.patch("pysysutils.collectors.cpu.psutil.cpu_percent", side_effect=[[12.5], [10.0, 15.0]])
    mocker.patch("pysysutils.collectors.cpu.psutil.cpu_count", side_effect=[4, 2])
    snap = collect_cpu()
    assert snap.percent == 12.5
    assert snap.count_logical == 4
    assert snap.count_physical == 2
    assert snap.per_cpu == [10.0, 15.0]
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `pytest tests/test_cpu.py -v`

- [ ] **Step 3: Implement collector**

```python
# src/pysysutils/collectors/cpu.py
import psutil
from pysysutils.models import CpuSnapshot


def collect_cpu(interval: float = 0.1) -> CpuSnapshot:
    percent = psutil.cpu_percent(interval=interval)
    per_cpu = psutil.cpu_percent(interval=0, percpu=True)
    return CpuSnapshot(
        percent=percent,
        per_cpu=per_cpu,
        count_logical=psutil.cpu_count(logical=True) or 0,
        count_physical=psutil.cpu_count(logical=False),
    )
```

- [ ] **Step 4: Run test — expect PASS**

Run: `pytest tests/test_cpu.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/collectors/ tests/test_cpu.py
git commit -m "feat: add CPU collector"
```

---

### Task 4: Memory collector

**Files:**
- Create: `src/pysysutils/collectors/memory.py`
- Create: `tests/test_memory.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_memory.py
from types import SimpleNamespace
from pysysutils.collectors.memory import collect_memory


def test_collect_memory(mocker):
    mocker.patch(
        "pysysutils.collectors.memory.psutil.virtual_memory",
        return_value=SimpleNamespace(total=16, available=8, used=8, free=4, percent=50.0),
    )
    mocker.patch(
        "pysysutils.collectors.memory.psutil.swap_memory",
        return_value=SimpleNamespace(total=4, used=1, free=3, percent=25.0),
    )
    snap = collect_memory()
    assert snap.total == 16
    assert snap.percent == 50.0
    assert snap.swap_percent == 25.0
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `pytest tests/test_memory.py -v`

- [ ] **Step 3: Implement**

```python
# src/pysysutils/collectors/memory.py
import psutil
from pysysutils.models import MemorySnapshot


def collect_memory() -> MemorySnapshot:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return MemorySnapshot(
        total=vm.total,
        available=vm.available,
        used=vm.used,
        free=vm.free,
        percent=vm.percent,
        swap_total=swap.total,
        swap_used=swap.used,
        swap_percent=swap.percent if swap.total else None,
    )
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/collectors/memory.py tests/test_memory.py
git commit -m "feat: add memory collector"
```

---

### Task 5: Process collector

**Files:**
- Create: `src/pysysutils/collectors/processes.py`
- Create: `tests/test_processes.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_processes.py
from types import SimpleNamespace
import psutil
from pysysutils.collectors.processes import collect_processes


def test_collect_processes_sorted_by_memory(mocker):
    proc_a = mocker.Mock()
    proc_a.info = {"pid": 1, "name": "a", "username": "u", "cpu_percent": 1.0, "memory_percent": 5.0, "status": "running"}
    proc_b = mocker.Mock()
    proc_b.info = {"pid": 2, "name": "b", "username": "u", "cpu_percent": 2.0, "memory_percent": 10.0, "status": "running"}

    mocker.patch("pysysutils.collectors.processes.psutil.process_iter", return_value=[proc_a, proc_b])
    snap = collect_processes(top=1, sort="memory")
    assert len(snap.processes) == 1
    assert snap.processes[0].pid == 2
    assert snap.processes[0].memory_percent == 10.0


def test_collect_processes_skips_access_denied(mocker):
    proc = mocker.Mock()
    proc.info = {}
    type(proc).info = property(lambda self: (_ for _ in ()).throw(psutil.AccessDenied(1)))
    mocker.patch("pysysutils.collectors.processes.psutil.process_iter", return_value=[proc])
    snap = collect_processes()
    assert snap.processes == []
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `pytest tests/test_processes.py -v`

- [ ] **Step 3: Implement**

```python
# src/pysysutils/collectors/processes.py
import psutil
from pysysutils.models import ProcessInfo, ProcessSnapshot


def collect_processes(top: int | None = 10, sort: str = "memory") -> ProcessSnapshot:
    processes: list[ProcessInfo] = []
    attrs = ["pid", "name", "username", "cpu_percent", "memory_percent", "status"]
    for proc in psutil.process_iter(attrs):
        try:
            info = proc.info
            processes.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=info.get("name") or "",
                    username=info.get("username"),
                    cpu_percent=info.get("cpu_percent"),
                    memory_percent=info.get("memory_percent") or 0.0,
                    status=info.get("status"),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    key = {"memory": lambda p: p.memory_percent, "cpu": lambda p: p.cpu_percent or 0.0}.get(sort, lambda p: p.memory_percent)
    processes.sort(key=key, reverse=True)
    if top is not None:
        processes = processes[:top]
    return ProcessSnapshot(processes=processes)
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/collectors/processes.py tests/test_processes.py
git commit -m "feat: add process collector with access-denied handling"
```

---

### Task 6: Disk collector

**Files:**
- Create: `src/pysysutils/collectors/disk.py`
- Create: `tests/test_disk.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_disk.py
from types import SimpleNamespace
from pysysutils.collectors.disk import collect_disk


def test_collect_disk(mocker):
    part = SimpleNamespace(device="/dev/sda1", mountpoint="/", fstype="ext4")
    usage = SimpleNamespace(total=100, used=50, free=50, percent=50.0)
    mocker.patch("pysysutils.collectors.disk.psutil.disk_partitions", return_value=[part])
    mocker.patch("pysysutils.collectors.disk.psutil.disk_usage", return_value=usage)
    snap = collect_disk()
    assert len(snap.partitions) == 1
    assert snap.partitions[0].mountpoint == "/"
    assert snap.partitions[0].percent == 50.0


def test_collect_disk_skips_permission_error(mocker):
    part = SimpleNamespace(device="X:", mountpoint="X:\\", fstype="NTFS")
    mocker.patch("pysysutils.collectors.disk.psutil.disk_partitions", return_value=[part])
    mocker.patch("pysysutils.collectors.disk.psutil.disk_usage", side_effect=PermissionError)
    snap = collect_disk()
    assert snap.partitions == []
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement**

```python
# src/pysysutils/collectors/disk.py
import psutil
from pysysutils.models import DiskPartition, DiskSnapshot


def collect_disk() -> DiskSnapshot:
    partitions: list[DiskPartition] = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        partitions.append(
            DiskPartition(
                device=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                total=usage.total,
                used=usage.used,
                free=usage.free,
                percent=usage.percent,
            )
        )
    return DiskSnapshot(partitions=partitions)
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/collectors/disk.py tests/test_disk.py
git commit -m "feat: add cross-platform disk collector"
```

---

### Task 7: Network collector

**Files:**
- Create: `src/pysysutils/collectors/network.py`
- Create: `tests/test_network.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_network.py
from types import SimpleNamespace
from pysysutils.collectors.network import collect_network, compute_rates


def test_collect_network(mocker):
    counters = SimpleNamespace(bytes_sent=1000, bytes_recv=2000, packets_sent=10, packets_recv=20)
    mocker.patch("pysysutils.collectors.network.psutil.net_io_counters", return_value=counters)
    snap = collect_network()
    assert snap.bytes_sent == 1000
    assert snap.bytes_recv == 2000


def test_compute_rates():
    prev = collect_network_result = type("S", (), {"bytes_sent": 1000, "bytes_recv": 2000})()
    curr = type("S", (), {"bytes_sent": 2000, "bytes_recv": 4000})()
    send, recv = compute_rates(prev, curr, elapsed=1.0)
    assert send == 1000.0
    assert recv == 2000.0
```

Note: adjust imports after implementing `collect_network` helper types.

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement**

```python
# src/pysysutils/collectors/network.py
import psutil
from pysysutils.models import NetworkSnapshot


def collect_network() -> NetworkSnapshot:
    c = psutil.net_io_counters()
    return NetworkSnapshot(
        bytes_sent=c.bytes_sent,
        bytes_recv=c.bytes_recv,
        packets_sent=getattr(c, "packets_sent", None),
        packets_recv=getattr(c, "packets_recv", None),
        send_rate_bps=None,
        recv_rate_bps=None,
    )


def compute_rates(
    previous: NetworkSnapshot, current: NetworkSnapshot, elapsed: float
) -> tuple[float, float]:
    if elapsed <= 0:
        return 0.0, 0.0
    send = (current.bytes_sent - previous.bytes_sent) / elapsed
    recv = (current.bytes_recv - previous.bytes_recv) / elapsed
    return max(send, 0.0), max(recv, 0.0)
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/collectors/network.py tests/test_network.py
git commit -m "feat: add network collector and rate helper"
```

---

### Task 8: CI workflow

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Add GitHub Actions workflow**

```yaml
name: test
on: [push, pull_request]
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.10", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest -v
```

- [ ] **Step 2: Run full test suite locally**

Run: `pytest -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add cross-platform test matrix"
```

---

## Phase 2 — CLI and Formatters

### Task 9: JSON formatter

**Files:**
- Create: `src/pysysutils/formatters/__init__.py`
- Create: `src/pysysutils/formatters/json_fmt.py`
- Create: `tests/test_formatters.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_formatters.py
import json
from pysysutils.models import CpuSnapshot
from pysysutils.formatters.json_fmt import to_json


def test_to_json_cpu_snapshot():
    snap = CpuSnapshot(percent=10.0, per_cpu=None, count_logical=4, count_physical=2)
    out = to_json(snap)
    data = json.loads(out)
    assert data["percent"] == 10.0
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement**

```python
# src/pysysutils/formatters/json_fmt.py
import json
from typing import Any


def to_json(obj: Any) -> str:
    if hasattr(obj, "to_dict"):
        payload = obj.to_dict()
    elif isinstance(obj, dict):
        payload = obj
    else:
        payload = {"value": obj}
    return json.dumps(payload, indent=2, default=str)
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/formatters/ tests/test_formatters.py
git commit -m "feat: add JSON formatter"
```

---

### Task 10: Table formatter

**Files:**
- Create: `src/pysysutils/formatters/table.py`
- Modify: `tests/test_formatters.py`

- [ ] **Step 1: Write failing test**

```python
# append to tests/test_formatters.py
from io import StringIO
from rich.console import Console
from pysysutils.models import CpuSnapshot, MemorySnapshot, SystemSnapshot, HealthLevel, BatterySnapshot, BatteryStatusSnapshot, BatteryHealthSnapshot, DiskSnapshot, NetworkSnapshot, ProcessSnapshot
from datetime import datetime, timezone
from pysysutils.formatters.table import render_snapshot


def test_render_snapshot_writes_cpu(capsys):
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
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement `render_snapshot` and helper render functions**

Implement sectioned Rich output for CPU, Memory, Disk, Network, Battery, Processes, Overall. Include byte-formatting helper:

```python
def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/formatters/table.py tests/test_formatters.py
git commit -m "feat: add Rich table formatter for snapshots"
```

---

### Task 11: Snapshot aggregator + CLI stub

**Files:**
- Create: `src/pysysutils/snapshot.py`
- Create: `src/pysysutils/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI test**

```python
# tests/test_cli.py
from typer.testing import CliRunner
from pysysutils.cli import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "snapshot" in result.stdout
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement snapshot builder**

```python
# src/pysysutils/snapshot.py
import socket
import sys
from datetime import datetime, timezone

from pysysutils.collectors.cpu import collect_cpu
from pysysutils.collectors.memory import collect_memory
from pysysutils.collectors.disk import collect_disk
from pysysutils.collectors.network import collect_network
from pysysutils.collectors.processes import collect_processes
from pysysutils.models import SystemSnapshot, HealthLevel


def build_snapshot(top: int = 10) -> SystemSnapshot:
    return SystemSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform=sys.platform,
        hostname=socket.gethostname(),
        cpu=collect_cpu(),
        memory=collect_memory(),
        disk=collect_disk(),
        network=collect_network(),
        battery=_battery_placeholder(),  # replaced in Phase 3
        top_processes=collect_processes(top=top),
        overall=HealthLevel.HEALTHY,
        issues=[],
    )
```

Add temporary `_battery_placeholder()` returning absent battery until Task 14.

- [ ] **Step 4: Implement minimal CLI**

```python
# src/pysysutils/cli.py
import typer
from rich.console import Console

from pysysutils.formatters.json_fmt import to_json
from pysysutils.formatters.table import render_snapshot
from pysysutils.snapshot import build_snapshot

app = typer.Typer(no_args_is_help=True, help="Cross-platform machine health monitor")
console = Console()


@app.command()
def snapshot(
    format: str = typer.Option("table", "--format", help="Output format: table or json"),
    top: int = typer.Option(10, "--top", help="Number of top processes"),
):
    """Print a one-shot system health report."""
    snap = build_snapshot(top=top)
    if format == "json":
        console.print(to_json(snap))
    else:
        render_snapshot(snap, console=console)
```

- [ ] **Step 5: Run test — expect PASS**

Run: `pytest tests/test_cli.py -v`

- [ ] **Step 6: Manual smoke test**

Run: `pysysutils snapshot --format json | head`
Expected: Valid JSON with `schema_version`, `cpu`, `memory`

- [ ] **Step 7: Commit**

```bash
git add src/pysysutils/snapshot.py src/pysysutils/cli.py tests/test_cli.py
git commit -m "feat: add snapshot command and aggregator"
```

---

### Task 12: Resource subcommands

**Files:**
- Modify: `src/pysysutils/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for `cpu`, `memory`, `disk`, `processes`, `network`**

```python
def test_cpu_json(mocker):
    from pysysutils.models import CpuSnapshot
    mocker.patch("pysysutils.cli.collect_cpu", return_value=CpuSnapshot(1.0, None, 1, 1))
    runner = CliRunner()
    result = runner.invoke(app, ["cpu", "--format", "json"])
    assert result.exit_code == 0
    assert "percent" in result.stdout
```

Import collectors at module level in cli or delegate to snapshot modules consistently.

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Add commands**

```python
@app.command()
def cpu(format: str = typer.Option("table", "--format")):
    from pysysutils.collectors.cpu import collect_cpu
    snap = collect_cpu()
    _emit(snap, format)

# Repeat for memory, disk, processes (--top, --sort), network
```

Extract shared `_emit(obj, format)` helper.

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/cli.py tests/test_cli.py
git commit -m "feat: add resource-specific CLI commands"
```

---

### Task 13: Watch command

**Files:**
- Modify: `src/pysysutils/cli.py`
- Modify: `src/pysysutils/snapshot.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test with mocked sleep/live**

Test that `watch --format json` invokes build_snapshot at least once (mock `time.sleep` to raise KeyboardInterrupt after first iteration).

- [ ] **Step 2: Implement watch**

```python
@app.command()
def watch(
    interval: float = typer.Option(2.0, "--interval"),
    format: str = typer.Option("table", "--format"),
    top: int = typer.Option(10, "--top"),
):
    import time
    from rich.live import Live

    try:
        if format == "json":
            while True:
                snap = build_snapshot(top=top)
                console.print(to_json(snap))
                time.sleep(interval)
        else:
            with Live(console=console, refresh_per_second=4) as live:
                while True:
                    snap = build_snapshot(top=top)
                    buf = Console(width=120, file=io.StringIO(), force_terminal=True)
                    render_snapshot(snap, console=buf)
                    live.update(buf.file.getvalue())
                    time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\nStopped.")
        raise typer.Exit(code=0)
```

Wire network rate updates inside `build_snapshot` or watch loop using `compute_rates`.

- [ ] **Step 3: Run tests — expect PASS**

- [ ] **Step 4: Commit**

```bash
git add src/pysysutils/cli.py src/pysysutils/snapshot.py tests/test_cli.py
git commit -m "feat: add live watch command"
```

---

## Phase 3 — Battery and Health Automation

### Task 14: Battery status collector

**Files:**
- Create: `src/pysysutils/collectors/battery_status.py`
- Create: `tests/test_battery_status.py`
- Modify: `src/pysysutils/snapshot.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_battery_status.py
import psutil
from pysysutils.collectors.battery_status import collect_battery_status, format_secsleft


def test_no_battery(mocker):
    mocker.patch("pysysutils.collectors.battery_status.psutil.sensors_battery", return_value=None)
    snap = collect_battery_status()
    assert snap.present is False


def test_battery_present(mocker):
    mocker.patch(
        "pysysutils.collectors.battery_status.psutil.sensors_battery",
        return_value=type("B", (), {"percent": 67.0, "power_plugged": False, "secsleft": 3600})(),
    )
    snap = collect_battery_status()
    assert snap.present is True
    assert snap.percent == 67.0


def test_format_secsleft_unknown():
    assert format_secsleft(psutil.POWER_TIME_UNKNOWN) == "unknown"
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement**

```python
# src/pysysutils/collectors/battery_status.py
import psutil
from pysysutils.models import BatteryStatusSnapshot


def format_secsleft(secsleft: int) -> str:
    if secsleft == psutil.POWER_TIME_UNLIMITED:
        return "charging"
    if secsleft == psutil.POWER_TIME_UNKNOWN:
        return "unknown"
    hours, rem = divmod(secsleft, 3600)
    minutes = rem // 60
    return f"{hours}h {minutes}m"


def collect_battery_status() -> BatteryStatusSnapshot:
    bat = psutil.sensors_battery()
    if bat is None:
        return BatteryStatusSnapshot(False, None, None, None, "n/a")
    return BatteryStatusSnapshot(
        present=True,
        percent=bat.percent,
        power_plugged=bat.power_plugged,
        secsleft=bat.secsleft if bat.secsleft not in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED) else None,
        secsleft_text=format_secsleft(bat.secsleft),
    )
```

- [ ] **Step 4: Integrate into `build_snapshot` and table formatter battery section**

- [ ] **Step 5: Run tests — expect PASS**

- [ ] **Step 6: Commit**

```bash
git add src/pysysutils/collectors/battery_status.py tests/test_battery_status.py src/pysysutils/snapshot.py
git commit -m "feat: add battery status collector"
```

---

### Task 15: Battery health backends

**Files:**
- Create: `src/pysysutils/collectors/battery_health/base.py`
- Create: `src/pysysutils/collectors/battery_health/linux.py`
- Create: `src/pysysutils/collectors/battery_health/darwin.py`
- Create: `src/pysysutils/collectors/battery_health/windows.py`
- Create: `src/pysysutils/collectors/battery_health/__init__.py`
- Create: `tests/fixtures/battery/linux_sysfs/`
- Create: `tests/test_battery_health.py`

- [ ] **Step 1: Write failing tests with fixture files**

```python
# tests/test_battery_health.py
from pathlib import Path
from pysysutils.collectors.battery_health.linux import LinuxBatteryHealthBackend


def test_linux_backend_parses_sysfs(tmp_path, mocker):
    bat = tmp_path / "BAT0"
    bat.mkdir()
    (bat / "energy_full_design").write_text("50000000\n")
    (bat / "energy_full").write_text("43500000\n")
    (bat / "cycle_count").write_text("412\n")
    mocker.patch("pysysutils.collectors.battery_health.linux._sysfs_root", return_value=tmp_path)
    snap = LinuxBatteryHealthBackend().collect()
    assert snap.available is True
    assert snap.health_percent == 87.0
    assert snap.cycle_count == 412
```

Add similar parse tests for darwin (mock subprocess output) and windows (mock powercfg HTML fixture).

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement backends**

`base.py` — ABC with `collect() -> BatteryHealthSnapshot`

`linux.py` — glob `BAT*` under `/sys/class/power_supply/`, read energy files (micro-watt-hours → mWh)

`darwin.py` — `subprocess.run(["ioreg", "-r", "-c", "AppleSmartBattery"], ...)` parse key/value pairs

`windows.py` — `subprocess.run(["powercfg", "/batteryreport", ...])` write temp HTML, parse `DESIGN CAPACITY` / `FULL CHARGE CAPACITY` / `CYCLE COUNT`

`__init__.py`:

```python
import sys
from pysysutils.collectors.battery_health.base import NoopBackend
from pysysutils.models import BatteryHealthSnapshot


def collect_battery_health() -> BatteryHealthSnapshot:
    platform = sys.platform
    if platform.startswith("linux"):
        from pysysutils.collectors.battery_health.linux import LinuxBatteryHealthBackend
        return LinuxBatteryHealthBackend().collect()
    if platform == "darwin":
        from pysysutils.collectors.battery_health.darwin import DarwinBatteryHealthBackend
        return DarwinBatteryHealthBackend().collect()
    if platform == "win32":
        from pysysutils.collectors.battery_health.windows import WindowsBatteryHealthBackend
        return WindowsBatteryHealthBackend().collect()
    return NoopBackend().collect()
```

All subprocess calls: `timeout=5`, catch exceptions → `NoopBackend` result.

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/collectors/battery_health/ tests/test_battery_health.py tests/fixtures/
git commit -m "feat: add platform-specific battery health backends"
```

---

### Task 16: Battery CLI command

**Files:**
- Modify: `src/pysysutils/cli.py`
- Modify: `src/pysysutils/snapshot.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
def test_battery_command_with_health(mocker):
    mocker.patch("pysysutils.cli.collect_battery_status", ...)
    mocker.patch("pysysutils.cli.collect_battery_health", ...)
    result = CliRunner().invoke(app, ["battery", "--health", "--format", "json"])
    assert result.exit_code == 0
```

- [ ] **Step 2: Implement `battery` command with `--health` flag**

Update `build_snapshot` to compose `BatterySnapshot(status=..., health=...)`.

- [ ] **Step 3: Run tests — expect PASS**

- [ ] **Step 4: Commit**

```bash
git add src/pysysutils/cli.py src/pysysutils/snapshot.py tests/test_cli.py
git commit -m "feat: add battery command with optional health details"
```

---

### Task 17: Health evaluator

**Files:**
- Create: `src/pysysutils/health.py`
- Create: `tests/test_health.py`
- Modify: `src/pysysutils/snapshot.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_health.py
from pysysutils.health import HealthThresholds, evaluate_snapshot, exit_code_for
from pysysutils.models import HealthLevel, SystemSnapshot
# build minimal snapshot fixtures at warning/critical boundaries


def test_memory_critical_sets_exit_code_2():
    # memory percent 96 with default thresholds
    ...
    assert exit_code_for(HealthLevel.CRITICAL) == 2


def test_no_battery_skipped_does_not_affect_overall():
    ...
```

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement**

```python
# src/pysysutils/health.py
from dataclasses import dataclass
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


def evaluate_snapshot(snap: SystemSnapshot, thresholds: HealthThresholds) -> tuple[HealthLevel, list[str]]:
    ...


def exit_code_for(level: HealthLevel) -> int:
    return {HealthLevel.HEALTHY: 0, HealthLevel.WARNING: 1, HealthLevel.CRITICAL: 2}.get(level, 1)
```

Implement severity aggregation: critical > warning > healthy; SKIPPED ignored.

Integrate into `build_snapshot` so `overall` and `issues` populate.

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/pysysutils/health.py tests/test_health.py src/pysysutils/snapshot.py
git commit -m "feat: add health threshold evaluation"
```

---

### Task 18: Check command

**Files:**
- Modify: `src/pysysutils/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for exit codes**

```python
def test_check_healthy_exits_0(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=healthy_snapshot)
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 0


def test_check_critical_exits_2(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=critical_snapshot)
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 2
```

- [ ] **Step 2: Implement**

```python
@app.command()
def check(
    format: str = typer.Option("table", "--format"),
    cpu_max: float | None = typer.Option(None, "--cpu-max"),
    mem_max: float | None = typer.Option(None, "--mem-max"),
    disk_max: float | None = typer.Option(None, "--disk-max"),
    battery_min: float | None = typer.Option(None, "--battery-min"),
    battery_health_min: float | None = typer.Option(None, "--battery-health-min"),
):
    thresholds = HealthThresholds(...)
    snap = build_snapshot()
    level, issues = evaluate_snapshot(snap, thresholds)
    snap.overall = level
    snap.issues = issues
    _emit(snap, format)
    raise typer.Exit(code=exit_code_for(level))
```

Map `--cpu-max` style flags to inverted thresholds (user specifies max allowed → internal warning/critical).

- [ ] **Step 3: Run tests — expect PASS**

- [ ] **Step 4: Commit**

```bash
git add src/pysysutils/cli.py tests/test_cli.py
git commit -m "feat: add check command with exit codes for automation"
```

---

## Phase 4 — Polish

### Task 19: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite README**

Include: install instructions, command reference (`snapshot`, `watch`, `check`, resource commands), JSON examples, exit code table, battery health platform notes, deprecation note for `py-sysutils-admin.py`.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document pysysutils CLI and migration from legacy script"
```

---

### Task 20: Network watch subcommand

**Files:**
- Modify: `src/pysysutils/cli.py`

- [ ] **Step 1: Add `--watch` to `network` command**

Loop with `compute_rates`, display send/recv in human units (Mbps).

- [ ] **Step 2: Manual smoke test**

Run: `pysysutils network --watch --interval 1` (Ctrl+C after 3 ticks)

- [ ] **Step 3: Commit**

```bash
git add src/pysysutils/cli.py
git commit -m "feat: add network watch mode with live rates"
```

---

### Task 21: Final verification

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`
Expected: All PASS

- [ ] **Step 2: Run CLI smoke commands**

```bash
pysysutils --help
pysysutils snapshot
pysysutils snapshot --format json
pysysutils battery --health
pysysutils check
```

- [ ] **Step 3: Verify acceptance criteria from design spec §16**

- [ ] **Step 4: Commit any fixes**

```bash
git commit -am "chore: final polish and verification fixes"
```

---

## Execution Handoff

**Plan complete.** Saved to `docs/superpowers/plans/2026-07-13-pysysutils-modernization.md`.

**Two execution options for the next session:**

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks
2. **Inline Execution** — run tasks sequentially in one session with checkpoints

**Suggested starting point:** Task 1 (package scaffold) on a new implementation branch e.g. `cursor/pysysutils-implementation-7b41`.

**Legacy script:** keep `py-sysutils-admin.py` until Task 21 complete; mark deprecated in README (Task 19).
