from datetime import datetime, timezone

from typer.testing import CliRunner
from pysysutils.cli import app
from pysysutils.health import HealthThresholds, evaluate_snapshot
from pysysutils.models import (
    BatteryHealthSnapshot,
    BatterySnapshot,
    BatteryStatusSnapshot,
    CpuSnapshot,
    DiskSnapshot,
    HealthLevel,
    MemorySnapshot,
    NetworkSnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)


def _system_snapshot(overall: HealthLevel = HealthLevel.HEALTHY, memory_percent: float = 50.0) -> SystemSnapshot:
    return SystemSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform="linux",
        hostname="test",
        cpu=CpuSnapshot(percent=10.0, per_cpu=None, count_logical=4, count_physical=2),
        memory=MemorySnapshot(1, 1, 1, 1, memory_percent, None, None, None),
        disk=DiskSnapshot(partitions=[]),
        network=NetworkSnapshot(0, 0, None, None, None, None),
        battery=BatterySnapshot(
            status=BatteryStatusSnapshot(False, None, None, None, "n/a"),
            health=BatteryHealthSnapshot(False, None, None, None, None, None),
        ),
        top_processes=ProcessSnapshot(processes=[]),
        overall=overall,
        issues=[],
    )


def _evaluated_snapshot(**kwargs) -> SystemSnapshot:
    snap = _system_snapshot(**kwargs)
    level, issues = evaluate_snapshot(snap, HealthThresholds())
    snap.overall = level
    snap.issues = issues
    return snap


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "snapshot" in result.stdout
    assert "check" in result.stdout
    assert "battery" in result.stdout


def test_cpu_json(mocker):
    mocker.patch("pysysutils.cli.collect_cpu", return_value=CpuSnapshot(1.0, None, 1, 1))
    runner = CliRunner()
    result = runner.invoke(app, ["cpu", "--format", "json"])
    assert result.exit_code == 0
    assert "percent" in result.stdout


def test_invalid_format_rejected():
    result = CliRunner().invoke(app, ["cpu", "--format", "xml"])
    assert result.exit_code != 0


def test_battery_command_with_health(mocker):
    mocker.patch(
        "pysysutils.cli.collect_battery_status",
        return_value=BatteryStatusSnapshot(True, 67.0, False, 3600, "1h 0m"),
    )
    mocker.patch(
        "pysysutils.cli.collect_battery_health",
        return_value=BatteryHealthSnapshot(True, 87.0, 412, 50000, 43500, "Normal"),
    )
    result = CliRunner().invoke(app, ["battery", "--health", "--format", "json"])
    assert result.exit_code == 0
    assert "health_percent" in result.stdout


def test_check_healthy_exits_0(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=_evaluated_snapshot())
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 0


def test_check_warning_exits_1(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=_evaluated_snapshot(memory_percent=86.0))
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 1


def test_check_critical_exits_2(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=_evaluated_snapshot(memory_percent=96.0))
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 2


def test_check_json_writes_stdout(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=_evaluated_snapshot())
    result = CliRunner().invoke(app, ["check", "--format", "json"])
    assert result.exit_code == 0
    assert "overall" in result.stdout
    assert result.stderr == ""


def test_check_table_writes_stderr(mocker):
    import io

    from rich.console import Console
    from pysysutils import cli

    buf = io.StringIO()
    mocker.patch.object(cli, "stderr_console", Console(file=buf, force_terminal=True, width=120))
    mocker.patch("pysysutils.cli.build_snapshot", return_value=_evaluated_snapshot())
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Overall" in buf.getvalue()


def test_check_invalid_threshold():
    result = CliRunner().invoke(app, ["check", "--cpu-max", "150"])
    assert result.exit_code != 0


def test_watch_json_interrupts(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=mocker.Mock(to_dict=lambda: {"ok": True}))
    mocker.patch("pysysutils.cli.time.sleep", side_effect=KeyboardInterrupt)
    runner = CliRunner()
    result = runner.invoke(app, ["watch", "--format", "json"])
    assert result.exit_code == 0
