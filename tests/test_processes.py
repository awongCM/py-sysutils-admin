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
