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
