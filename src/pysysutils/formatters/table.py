from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.text import Text

from pysysutils.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    NetworkSnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _render_cpu(snap: CpuSnapshot) -> Table:
    table = Table(title="CPU", show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Usage", f"{snap.percent:.1f}%")
    table.add_row("Logical cores", str(snap.count_logical))
    if snap.count_physical is not None:
        table.add_row("Physical cores", str(snap.count_physical))
    return table


def _render_memory(snap: MemorySnapshot) -> Table:
    table = Table(title="Memory", show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Total", format_bytes(snap.total))
    table.add_row("Used", format_bytes(snap.used))
    table.add_row("Available", format_bytes(snap.available))
    table.add_row("Usage", f"{snap.percent:.1f}%")
    if snap.swap_total:
        table.add_row("Swap usage", f"{snap.swap_percent:.1f}%" if snap.swap_percent is not None else "n/a")
    return table


def _render_disk(snap: DiskSnapshot) -> Table:
    table = Table(title="Disk", show_header=True, header_style="bold")
    table.add_column("Mount")
    table.add_column("Used")
    table.add_column("Total")
    table.add_column("Usage")
    for part in snap.partitions:
        table.add_row(part.mountpoint, format_bytes(part.used), format_bytes(part.total), f"{part.percent:.1f}%")
    if not snap.partitions:
        table.add_row("—", "—", "—", "—")
    return table


def _render_network(snap: NetworkSnapshot) -> Table:
    table = Table(title="Network", show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Bytes sent", format_bytes(snap.bytes_sent))
    table.add_row("Bytes recv", format_bytes(snap.bytes_recv))
    if snap.send_rate_bps is not None:
        table.add_row("Send rate", f"{snap.send_rate_bps / 1024:.1f} KB/s")
    if snap.recv_rate_bps is not None:
        table.add_row("Recv rate", f"{snap.recv_rate_bps / 1024:.1f} KB/s")
    return table


def _render_battery(snap: BatterySnapshot) -> Table:
    table = Table(title="Battery", show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value")
    if not snap.status.present:
        table.add_row("Status", "Not present")
        return table
    if snap.status.percent is not None:
        table.add_row("Charge", f"{snap.status.percent:.0f}%")
    if snap.status.power_plugged is not None:
        table.add_row("Power", "Plugged in" if snap.status.power_plugged else "On battery")
    table.add_row("Time left", snap.status.secsleft_text)
    if snap.health.available and snap.health.health_percent is not None:
        table.add_row("Health", f"{snap.health.health_percent:.0f}%")
    return table


def _render_processes(snap: ProcessSnapshot) -> Table:
    table = Table(title="Top Processes", show_header=True, header_style="bold")
    table.add_column("PID")
    table.add_column("Name")
    table.add_column("CPU %")
    table.add_column("Mem %")
    for proc in snap.processes:
        cpu = f"{proc.cpu_percent:.1f}" if proc.cpu_percent is not None else "—"
        table.add_row(str(proc.pid), proc.name, cpu, f"{proc.memory_percent:.1f}")
    if not snap.processes:
        table.add_row("—", "—", "—", "—")
    return table


def render_snapshot(snap: SystemSnapshot, console: Console | None = None) -> None:
    out = console or Console()
    out.print(_render_cpu(snap.cpu))
    out.print(_render_memory(snap.memory))
    out.print(_render_disk(snap.disk))
    out.print(_render_network(snap.network))
    out.print(_render_battery(snap.battery))
    out.print(_render_processes(snap.top_processes))
    overall_style = {"healthy": "green", "warning": "yellow", "critical": "red"}.get(
        snap.overall.value, "white"
    )
    out.print(Text(f"Overall: {snap.overall.value}", style=f"bold {overall_style}"))
    for issue in snap.issues:
        out.print(Text(f"  • {issue}", style="yellow"))
