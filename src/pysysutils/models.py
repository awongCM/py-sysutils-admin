from __future__ import annotations

from dataclasses import asdict, dataclass, field
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


@dataclass
class MemorySnapshot:
    total: int
    available: int
    used: int
    free: int
    percent: float
    swap_total: int | None
    swap_used: int | None
    swap_percent: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessInfo:
    pid: int
    name: str
    username: str | None
    cpu_percent: float | None
    memory_percent: float
    status: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessSnapshot:
    processes: list[ProcessInfo]

    def to_dict(self) -> dict[str, Any]:
        return {"processes": [p.to_dict() for p in self.processes]}


@dataclass
class DiskPartition:
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiskSnapshot:
    partitions: list[DiskPartition]

    def to_dict(self) -> dict[str, Any]:
        return {"partitions": [p.to_dict() for p in self.partitions]}


@dataclass
class NetworkSnapshot:
    bytes_sent: int
    bytes_recv: int
    packets_sent: int | None
    packets_recv: int | None
    send_rate_bps: float | None
    recv_rate_bps: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BatteryStatusSnapshot:
    present: bool
    percent: float | None
    power_plugged: bool | None
    secsleft: int | None
    secsleft_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BatteryHealthSnapshot:
    available: bool
    health_percent: float | None
    cycle_count: int | None
    design_capacity_mwh: int | None
    full_charge_capacity_mwh: int | None
    condition: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BatterySnapshot:
    status: BatteryStatusSnapshot
    health: BatteryHealthSnapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.to_dict(),
            "health": self.health.to_dict(),
        }


@dataclass
class SystemSnapshot:
    timestamp: datetime
    platform: str
    hostname: str
    cpu: CpuSnapshot
    memory: MemorySnapshot
    disk: DiskSnapshot
    network: NetworkSnapshot
    battery: BatterySnapshot
    top_processes: ProcessSnapshot
    overall: HealthLevel
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "timestamp": self.timestamp.isoformat(),
            "platform": self.platform,
            "hostname": self.hostname,
            "cpu": self.cpu.to_dict(),
            "memory": self.memory.to_dict(),
            "disk": self.disk.to_dict(),
            "network": self.network.to_dict(),
            "battery": self.battery.to_dict(),
            "top_processes": self.top_processes.to_dict(),
            "overall": self.overall.value,
            "issues": list(self.issues),
        }
