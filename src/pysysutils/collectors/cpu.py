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
