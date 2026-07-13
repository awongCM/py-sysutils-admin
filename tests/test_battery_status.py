import psutil
from pysysutils.collectors.battery_status import collect_battery_status, format_secsleft


def test_no_battery(mocker):
    mocker.patch("pysysutils.collectors.battery_status.psutil.sensors_battery", return_value=None)
    snap = collect_battery_status()
    assert snap.present is False


def test_battery_present(mocker):
    mocker.patch(
        "pysysutils.collectors.battery_status.psutil.sensors_battery",
        return_value=type("B", (), {"percent": 67.0, "power_plugged": False, "secsleft": 3600})(),
    )
    snap = collect_battery_status()
    assert snap.present is True
    assert snap.percent == 67.0


def test_format_secsleft_unknown():
    assert format_secsleft(psutil.POWER_TIME_UNKNOWN) == "unknown"
