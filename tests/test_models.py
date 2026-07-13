from pysysutils.models import HealthLevel, CpuSnapshot


def test_cpu_snapshot_to_dict():
    snap = CpuSnapshot(percent=42.5, per_cpu=[10.0, 20.0], count_logical=4, count_physical=2)
    d = snap.to_dict()
    assert d["percent"] == 42.5
    assert d["count_logical"] == 4
    assert d["per_cpu"] == [10.0, 20.0]


def test_health_level_values():
    assert HealthLevel.HEALTHY.value == "healthy"
    assert HealthLevel.CRITICAL.value == "critical"
