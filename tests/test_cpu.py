from pysysutils.collectors.cpu import collect_cpu


def test_collect_cpu(mocker):
    mocker.patch("pysysutils.collectors.cpu.psutil.cpu_percent", side_effect=[12.5, [10.0, 15.0]])
    mocker.patch("pysysutils.collectors.cpu.psutil.cpu_count", side_effect=[4, 2])
    snap = collect_cpu()
    assert snap.percent == 12.5
    assert snap.count_logical == 4
    assert snap.count_physical == 2
    assert snap.per_cpu == [10.0, 15.0]
