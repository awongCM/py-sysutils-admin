from pysysutils.collectors.battery_health.darwin import DarwinBatteryHealthBackend, _parse_ioreg_output
from pysysutils.collectors.battery_health.linux import LinuxBatteryHealthBackend
from pysysutils.collectors.battery_health.windows import WindowsBatteryHealthBackend, _parse_battery_report


def test_linux_backend_parses_sysfs(tmp_path, mocker):
    bat = tmp_path / "BAT0"
    bat.mkdir()
    (bat / "energy_full_design").write_text("50000000\n")
    (bat / "energy_full").write_text("43500000\n")
    (bat / "cycle_count").write_text("412\n")
    mocker.patch("pysysutils.collectors.battery_health.linux._sysfs_root", return_value=tmp_path)
    snap = LinuxBatteryHealthBackend().collect()
    assert snap.available is True
    assert snap.health_percent == 87.0
    assert snap.cycle_count == 412


def test_darwin_backend_parses_ioreg(mocker):
    ioreg_output = '''
    "AppleSmartBattery" = {
        "DesignCapacity" = 5000
        "MaxCapacity" = 4350
        "CycleCount" = 412
    }
    '''
    mocker.patch(
        "pysysutils.collectors.battery_health.darwin.subprocess.run",
        return_value=mocker.Mock(returncode=0, stdout=ioreg_output),
    )
    snap = DarwinBatteryHealthBackend().collect()
    assert snap.available is True
    assert snap.health_percent == 87.0
    assert snap.cycle_count == 412


def test_parse_ioreg_missing_data():
    snap = _parse_ioreg_output('"Foo" = 1')
    assert snap.available is False


def test_windows_backend_parses_html(mocker):
    html = """
    <tr><td>DESIGN CAPACITY</td><td>50,000 mWh</td></tr>
    <tr><td>FULL CHARGE CAPACITY</td><td>43,500 mWh</td></tr>
    <tr><td>CYCLE COUNT</td><td>412</td></tr>
    """
    mocker.patch(
        "pysysutils.collectors.battery_health.windows.subprocess.run",
        return_value=mocker.Mock(returncode=0),
    )
    mocker.patch(
        "pysysutils.collectors.battery_health.windows.Path.read_text",
        return_value=html,
    )
    mocker.patch("pysysutils.collectors.battery_health.windows.Path.exists", return_value=True)
    mocker.patch("pysysutils.collectors.battery_health.windows.Path.unlink")
    snap = WindowsBatteryHealthBackend().collect()
    assert snap.available is True
    assert snap.health_percent == 87.0
    assert snap.cycle_count == 412


def test_parse_battery_report_missing():
    snap = _parse_battery_report("<html></html>")
    assert snap.available is False
