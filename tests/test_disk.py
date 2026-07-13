from types import SimpleNamespace
from pysysutils.collectors.disk import collect_disk


def test_collect_disk(mocker):
    part = SimpleNamespace(device="/dev/sda1", mountpoint="/", fstype="ext4")
    usage = SimpleNamespace(total=100, used=50, free=50, percent=50.0)
    mocker.patch("pysysutils.collectors.disk.psutil.disk_partitions", return_value=[part])
    mocker.patch("pysysutils.collectors.disk.psutil.disk_usage", return_value=usage)
    snap = collect_disk()
    assert len(snap.partitions) == 1
    assert snap.partitions[0].mountpoint == "/"
    assert snap.partitions[0].percent == 50.0


def test_collect_disk_skips_permission_error(mocker):
    part = SimpleNamespace(device="X:", mountpoint="X:\\", fstype="NTFS")
    mocker.patch("pysysutils.collectors.disk.psutil.disk_partitions", return_value=[part])
    mocker.patch("pysysutils.collectors.disk.psutil.disk_usage", side_effect=PermissionError)
    snap = collect_disk()
    assert snap.partitions == []
