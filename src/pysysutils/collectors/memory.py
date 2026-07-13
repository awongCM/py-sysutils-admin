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
