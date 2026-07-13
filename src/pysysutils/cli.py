import io
import time

import typer
from rich.console import Console
from rich.live import Live

from pysysutils.collectors.cpu import collect_cpu
from pysysutils.collectors.disk import collect_disk
from pysysutils.collectors.memory import collect_memory
from pysysutils.collectors.network import collect_network
from pysysutils.collectors.processes import collect_processes
from pysysutils.collectors.battery_status import collect_battery_status
from pysysutils.collectors.battery_health import collect_battery_health
from pysysutils.health import evaluate_snapshot, exit_code_for, thresholds_from_cli
from pysysutils.formatters.json_fmt import to_json
from pysysutils.formatters.table import (
    _render_battery,
    _render_cpu,
    _render_disk,
    _render_memory,
    _render_network,
    _render_processes,
    render_snapshot,
)
from pysysutils.models import (
    BatteryHealthSnapshot,
    BatterySnapshot,
    BatteryStatusSnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    NetworkSnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)
from pysysutils.snapshot import build_snapshot

app = typer.Typer(no_args_is_help=True, help="Cross-platform machine health monitor")
console = Console()


def _emit_table(obj: object) -> None:
    if isinstance(obj, SystemSnapshot):
        render_snapshot(obj, console=console)
    elif isinstance(obj, CpuSnapshot):
        console.print(_render_cpu(obj))
    elif isinstance(obj, MemorySnapshot):
        console.print(_render_memory(obj))
    elif isinstance(obj, DiskSnapshot):
        console.print(_render_disk(obj))
    elif isinstance(obj, NetworkSnapshot):
        console.print(_render_network(obj))
    elif isinstance(obj, ProcessSnapshot):
        console.print(_render_processes(obj))
    elif isinstance(obj, BatterySnapshot):
        console.print(_render_battery(obj))
    else:
        console.print(str(obj))


def _emit(obj: object, format: str) -> None:
    if format == "json":
        console.print(to_json(obj))
    else:
        _emit_table(obj)


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


@app.command()
def cpu(format: str = typer.Option("table", "--format")):
    """Show CPU usage."""
    _emit(collect_cpu(), format)


@app.command()
def memory(format: str = typer.Option("table", "--format")):
    """Show memory usage."""
    _emit(collect_memory(), format)


@app.command()
def disk(format: str = typer.Option("table", "--format")):
    """Show disk usage."""
    _emit(collect_disk(), format)


@app.command()
def processes(
    format: str = typer.Option("table", "--format"),
    top: int = typer.Option(10, "--top"),
    sort: str = typer.Option("memory", "--sort"),
):
    """Show top processes."""
    _emit(collect_processes(top=top, sort=sort), format)


@app.command()
def network(format: str = typer.Option("table", "--format")):
    """Show network counters."""
    _emit(collect_network(), format)


@app.command()
def battery(
    format: str = typer.Option("table", "--format"),
    health: bool = typer.Option(False, "--health", help="Include battery health metrics"),
):
    """Show battery status and optional health details."""
    snap = BatterySnapshot(
        status=collect_battery_status(),
        health=collect_battery_health() if health else BatteryHealthSnapshot(
            False, None, None, None, None, None
        ),
    )
    _emit(snap, format)


@app.command()
def check(
    format: str = typer.Option("table", "--format"),
    cpu_max: float | None = typer.Option(None, "--cpu-max"),
    mem_max: float | None = typer.Option(None, "--mem-max"),
    disk_max: float | None = typer.Option(None, "--disk-max"),
    battery_min: float | None = typer.Option(None, "--battery-min"),
    battery_health_min: float | None = typer.Option(None, "--battery-health-min"),
):
    """Automation health gate with configurable thresholds and exit codes."""
    thresholds = thresholds_from_cli(
        cpu_max=cpu_max,
        mem_max=mem_max,
        disk_max=disk_max,
        battery_min=battery_min,
        battery_health_min=battery_health_min,
    )
    snap = build_snapshot()
    level, issues = evaluate_snapshot(snap, thresholds)
    snap.overall = level
    snap.issues = issues
    _emit(snap, format)
    raise typer.Exit(code=exit_code_for(level))


@app.command()
def watch(
    interval: float = typer.Option(2.0, "--interval"),
    format: str = typer.Option("table", "--format"),
    top: int = typer.Option(10, "--top"),
):
    """Live refreshing system dashboard."""
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
