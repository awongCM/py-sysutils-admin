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
