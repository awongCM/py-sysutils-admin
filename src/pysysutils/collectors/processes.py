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

    key = {"memory": lambda p: p.memory_percent, "cpu": lambda p: p.cpu_percent or 0.0}.get(
        sort, lambda p: p.memory_percent
    )
    processes.sort(key=key, reverse=True)
    if top is not None:
        processes = processes[:top]
    return ProcessSnapshot(processes=processes)
